package aegis.portfolio;

import aegis.common.Instrument;
import aegis.common.InstrumentRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class PaperTradingService {

    private final PaperAccountRepository accountRepo;
    private final PaperOrderRepository orderRepo;
    private final PaperPositionRepository positionRepo;
    private final InstrumentRepository instrumentRepo;

    public PaperTradingService(PaperAccountRepository accountRepo,
                               PaperOrderRepository orderRepo,
                               PaperPositionRepository positionRepo,
                               InstrumentRepository instrumentRepo) {
        this.accountRepo = accountRepo;
        this.orderRepo = orderRepo;
        this.positionRepo = positionRepo;
        this.instrumentRepo = instrumentRepo;
    }

    public PaperAccount getDefaultAccount() {
        return accountRepo.findByName("default")
                .orElseGet(() -> {
                    PaperAccount a = new PaperAccount();
                    a.setName("default");
                    a.setCash(new BigDecimal("1000000.00"));
                    a.setEquity(new BigDecimal("1000000.00"));
                    a.setCreatedAt(Instant.now());
                    a.setUpdatedAt(Instant.now());
                    return accountRepo.save(a);
                });
    }

    @Transactional
    public PaperOrder placeOrder(String symbol, String side, String orderType,
                                 int quantity, BigDecimal limitPrice, BigDecimal stopPrice,
                                 BigDecimal marketPrice) {
        PaperAccount account = getDefaultAccount();
        Instrument inst = instrumentRepo.findById(symbol).orElseGet(() -> {
            Instrument created = new Instrument();
            created.setSymbol(symbol);
            created.setName(symbol);
            created.setExchange("NSE");
            created.setLotSize(1);
            created.setIsActive(true);
            return instrumentRepo.save(created);
        });

        int lotSize = inst.getLotSize() != null ? inst.getLotSize() : 1;
        // Round down to nearest valid lot
        int adjustedQty = (quantity / lotSize) * lotSize;
        if (adjustedQty <= 0) {
            throw new IllegalArgumentException("Quantity must be at least one lot (" + lotSize + ")");
        }

        BigDecimal price = marketPrice != null ? marketPrice :
                (limitPrice != null ? limitPrice : BigDecimal.valueOf(100));

        // Unlimited paper capital — size by lot only (product decision)
        BigDecimal cost = price.multiply(BigDecimal.valueOf(adjustedQty));

        PaperOrder order = new PaperOrder();
        order.setAccountId(account.getId());
        order.setSymbol(symbol);
        order.setSide(side.toUpperCase());
        order.setOrderType(orderType.toUpperCase());
        order.setQuantity(adjustedQty);
        order.setLimitPrice(limitPrice);
        order.setStopPrice(stopPrice);
        order.setCreatedAt(Instant.now());
        order.setUpdatedAt(Instant.now());

        // Immediate fill for MARKET / for simplicity also for LIMIT at market
        order.setFilledQty(adjustedQty);
        order.setAvgFillPrice(price);
        order.setStatus("FILLED");
        order = orderRepo.save(order);

        // Update position & cash in same transaction
        updatePositionAndCash(account, symbol, side, adjustedQty, price);

        return order;
    }

    private void updatePositionAndCash(PaperAccount account, String symbol, String side,
                                       int qty, BigDecimal price) {
        PaperPosition pos = positionRepo.findByAccountIdAndSymbol(account.getId(), symbol)
                .orElseGet(() -> {
                    PaperPosition p = new PaperPosition();
                    p.setAccountId(account.getId());
                    p.setSymbol(symbol);
                    p.setQuantity(0);
                    p.setAvgCost(BigDecimal.ZERO);
                    return p;
                });

        if ("BUY".equalsIgnoreCase(side)) {
            BigDecimal totalCost = pos.getAvgCost().multiply(BigDecimal.valueOf(pos.getQuantity()))
                    .add(price.multiply(BigDecimal.valueOf(qty)));
            int newQty = pos.getQuantity() + qty;
            pos.setQuantity(newQty);
            pos.setAvgCost(newQty > 0 ? totalCost.divide(BigDecimal.valueOf(newQty), 4, RoundingMode.HALF_UP) : BigDecimal.ZERO);
            account.setCash(account.getCash().subtract(price.multiply(BigDecimal.valueOf(qty))));
        } else {
            if (pos.getQuantity() < qty) {
                throw new IllegalArgumentException("Insufficient position to sell");
            }
            pos.setQuantity(pos.getQuantity() - qty);
            account.setCash(account.getCash().add(price.multiply(BigDecimal.valueOf(qty))));
            if (pos.getQuantity() == 0) {
                pos.setAvgCost(BigDecimal.ZERO);
            }
        }
        pos.setUpdatedAt(Instant.now());
        positionRepo.save(pos);

        // Recalc equity (cash + positions at cost for simplicity)
        BigDecimal positionsValue = positionRepo.findByAccountId(account.getId()).stream()
                .map(p -> p.getAvgCost().multiply(BigDecimal.valueOf(p.getQuantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        account.setEquity(account.getCash().add(positionsValue));
        account.setUpdatedAt(Instant.now());
        accountRepo.save(account);
    }

    public List<PaperPosition> getPositions() {
        return positionRepo.findByAccountId(getDefaultAccount().getId());
    }

    public List<PaperOrder> getOrders() {
        return orderRepo.findByAccountIdOrderByCreatedAtDesc(getDefaultAccount().getId());
    }

    public Map<String, Object> getSummary() {
        PaperAccount a = getDefaultAccount();
        List<PaperPosition> positions = getPositions();
        Map<String, Object> summary = new HashMap<>();
        summary.put("accountId", a.getId());
        summary.put("cash", a.getCash());
        summary.put("equity", a.getEquity());
        summary.put("positions", positions);
        summary.put("positionCount", positions.size());
        return summary;
    }
}
