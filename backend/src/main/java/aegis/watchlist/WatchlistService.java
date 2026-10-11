package aegis.watchlist;

import aegis.common.Instrument;
import aegis.common.InstrumentRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.*;

@Service
public class WatchlistService {

    private final WatchlistRepository watchlistRepo;
    private final InstrumentRepository instrumentRepo;

    public WatchlistService(WatchlistRepository watchlistRepo, InstrumentRepository instrumentRepo) {
        this.watchlistRepo = watchlistRepo;
        this.instrumentRepo = instrumentRepo;
    }

    public List<Map<String, Object>> list() {
        List<WatchlistEntry> entries = watchlistRepo.findAllByOrderByAddedAtDesc();
        List<Map<String, Object>> out = new ArrayList<>();
        for (WatchlistEntry e : entries) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("symbol", e.getSymbol());
            row.put("notes", e.getNotes());
            row.put("addedAt", e.getAddedAt());
            instrumentRepo.findById(e.getSymbol()).ifPresent(inst -> {
                row.put("name", inst.getName());
                row.put("sector", inst.getSector());
                row.put("lotSize", inst.getLotSize());
                row.put("exchange", inst.getExchange());
            });
            out.add(row);
        }
        return out;
    }

    @Transactional
    public Map<String, Object> add(String symbol, String name, String sector, Integer lotSize, String notes) {
        String sym = symbol.trim().toUpperCase();
        if (sym.isEmpty()) {
            throw new IllegalArgumentException("Symbol is required");
        }
        // Strip .NS / .BO if user pasted Yahoo form
        if (sym.endsWith(".NS") || sym.endsWith(".BO")) {
            sym = sym.substring(0, sym.lastIndexOf('.'));
        }

        Instrument inst = instrumentRepo.findById(sym).orElse(null);
        if (inst == null) {
            inst = new Instrument();
            inst.setSymbol(sym);
            inst.setName(name != null && !name.isBlank() ? name : sym);
            inst.setExchange("NSE");
            inst.setSector(sector != null && !sector.isBlank() ? sector : "Unknown");
            inst.setLotSize(lotSize != null && lotSize > 0 ? lotSize : 1);
            inst.setIsActive(true);
            inst.setCreatedAt(Instant.now());
            instrumentRepo.save(inst);
        } else {
            inst.setIsActive(true);
            if (name != null && !name.isBlank()) inst.setName(name);
            if (sector != null && !sector.isBlank()) inst.setSector(sector);
            if (lotSize != null && lotSize > 0) inst.setLotSize(lotSize);
            instrumentRepo.save(inst);
        }

        WatchlistEntry entry = watchlistRepo.findById(sym).orElse(new WatchlistEntry());
        entry.setSymbol(sym);
        entry.setNotes(notes);
        entry.setAddedAt(Instant.now());
        watchlistRepo.save(entry);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("symbol", sym);
        result.put("name", inst.getName());
        result.put("sector", inst.getSector());
        result.put("lotSize", inst.getLotSize());
        result.put("notes", notes);
        result.put("addedAt", entry.getAddedAt());
        return result;
    }

    @Transactional
    public boolean remove(String symbol) {
        String sym = symbol.trim().toUpperCase();
        if (sym.endsWith(".NS") || sym.endsWith(".BO")) {
            sym = sym.substring(0, sym.lastIndexOf('.'));
        }
        if (!watchlistRepo.existsById(sym)) {
            return false;
        }
        watchlistRepo.deleteById(sym);
        return true;
    }

    public boolean contains(String symbol) {
        return watchlistRepo.existsById(symbol.trim().toUpperCase());
    }
}
