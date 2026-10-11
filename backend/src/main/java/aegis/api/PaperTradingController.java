package aegis.api;

import aegis.common.ApiResponse;
import aegis.portfolio.PaperOrder;
import aegis.portfolio.PaperPosition;
import aegis.portfolio.PaperTradingService;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/paper")
public class PaperTradingController {

    private final PaperTradingService service;

    public PaperTradingController(PaperTradingService service) {
        this.service = service;
    }

    public record PlaceOrderRequest(
            String symbol,
            String side,
            String orderType,
            int quantity,
            BigDecimal limitPrice,
            BigDecimal stopPrice,
            BigDecimal marketPrice
    ) {}

    @PostMapping("/orders")
    public ApiResponse<PaperOrder> placeOrder(@RequestBody PlaceOrderRequest req) {
        try {
            PaperOrder order = service.placeOrder(
                    req.symbol(), req.side(), req.orderType() != null ? req.orderType() : "MARKET",
                    req.quantity(), req.limitPrice(), req.stopPrice(),
                    req.marketPrice() != null ? req.marketPrice() : BigDecimal.valueOf(1000)
            );
            return ApiResponse.ok("Order filled", order);
        } catch (IllegalArgumentException e) {
            return ApiResponse.error(e.getMessage());
        }
    }

    @GetMapping("/orders")
    public ApiResponse<List<PaperOrder>> orders() {
        return ApiResponse.ok(service.getOrders());
    }

    @GetMapping("/positions")
    public ApiResponse<List<PaperPosition>> positions() {
        return ApiResponse.ok(service.getPositions());
    }

    @GetMapping("/summary")
    public ApiResponse<Map<String, Object>> summary() {
        return ApiResponse.ok(service.getSummary());
    }
}
