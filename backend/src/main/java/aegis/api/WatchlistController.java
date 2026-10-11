package aegis.api;

import aegis.common.ApiResponse;
import aegis.watchlist.WatchlistService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/watchlist")
public class WatchlistController {

    private final WatchlistService service;

    public WatchlistController(WatchlistService service) {
        this.service = service;
    }

    public record AddRequest(
            String symbol,
            String name,
            String sector,
            Integer lotSize,
            String notes
    ) {}

    @GetMapping
    public ApiResponse<List<Map<String, Object>>> list() {
        return ApiResponse.ok(service.list());
    }

    @PostMapping
    public ApiResponse<Map<String, Object>> add(@RequestBody AddRequest req) {
        try {
            if (req.symbol() == null || req.symbol().isBlank()) {
                return ApiResponse.error("symbol is required");
            }
            Map<String, Object> entry = service.add(
                    req.symbol(), req.name(), req.sector(), req.lotSize(), req.notes());
            return ApiResponse.ok("Added to watchlist", entry);
        } catch (IllegalArgumentException e) {
            return ApiResponse.error(e.getMessage());
        }
    }

    @DeleteMapping("/{symbol}")
    public ApiResponse<String> remove(@PathVariable String symbol) {
        boolean removed = service.remove(symbol);
        if (!removed) {
            return ApiResponse.error("Symbol not on watchlist: " + symbol);
        }
        return ApiResponse.ok("Removed from watchlist", symbol.toUpperCase());
    }
}
