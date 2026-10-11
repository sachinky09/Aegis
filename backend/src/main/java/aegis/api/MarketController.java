package aegis.api;

import aegis.common.ApiResponse;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/market")
public class MarketController {

    private final JdbcTemplate jdbc;

    public MarketController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @GetMapping("/ticks/{symbol}")
    public ApiResponse<List<Map<String, Object>>> ticks(
            @PathVariable String symbol,
            @RequestParam(defaultValue = "50") int limit) {
        String sql = """
            SELECT time, symbol, price, volume, bid, ask
            FROM market_ticks
            WHERE symbol = ?
            ORDER BY time DESC
            LIMIT ?
            """;
        List<Map<String, Object>> rows = jdbc.queryForList(sql, symbol.toUpperCase(), limit);
        return ApiResponse.ok(rows);
    }

    @GetMapping("/candles/{symbol}")
    public ApiResponse<List<Map<String, Object>>> candles(
            @PathVariable String symbol,
            @RequestParam(defaultValue = "1d") String timeframe,
            @RequestParam(defaultValue = "100") int limit) {
        String sql = """
            SELECT time, symbol, timeframe, open, high, low, close, volume
            FROM candles
            WHERE symbol = ? AND timeframe = ?
            ORDER BY time DESC
            LIMIT ?
            """;
        List<Map<String, Object>> rows = jdbc.queryForList(sql, symbol.toUpperCase(), timeframe, limit);
        return ApiResponse.ok(rows);
    }

    @PostMapping("/ticks")
    public ApiResponse<String> ingestTick(@RequestBody Map<String, Object> tick) {
        String sql = """
            INSERT INTO market_ticks (time, symbol, price, volume, bid, ask)
            VALUES (NOW(), ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING
            """;
        jdbc.update(sql,
                tick.getOrDefault("symbol", "UNKNOWN").toString().toUpperCase(),
                tick.get("price"),
                tick.getOrDefault("volume", 0),
                tick.get("bid"),
                tick.get("ask"));
        return ApiResponse.ok("Tick ingested");
    }
}
