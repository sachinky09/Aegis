package aegis.api;

import aegis.common.ApiResponse;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/signals")
public class SignalController {

    private final JdbcTemplate jdbc;

    public SignalController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @GetMapping
    public ApiResponse<List<Map<String, Object>>> list(
            @RequestParam(required = false) String symbol,
            @RequestParam(defaultValue = "50") int limit) {
        String sql;
        List<Map<String, Object>> rows;
        if (symbol != null && !symbol.isBlank()) {
            sql = """
                SELECT id, symbol, signal_type, direction, strength, generated_at, status, metadata
                FROM signals
                WHERE symbol = ?
                ORDER BY generated_at DESC
                LIMIT ?
                """;
            rows = jdbc.queryForList(sql, symbol.toUpperCase(), limit);
        } else {
            sql = """
                SELECT id, symbol, signal_type, direction, strength, generated_at, status, metadata
                FROM signals
                ORDER BY generated_at DESC
                LIMIT ?
                """;
            rows = jdbc.queryForList(sql, limit);
        }
        return ApiResponse.ok(rows);
    }

    @PostMapping
    public ApiResponse<String> create(@RequestBody Map<String, Object> body) {
        String sql = """
            INSERT INTO signals (symbol, signal_type, direction, strength, metadata, status)
            VALUES (?, ?, ?, ?, ?::jsonb, 'ACTIVE')
            """;
        jdbc.update(sql,
                body.get("symbol").toString().toUpperCase(),
                body.getOrDefault("signalType", "TECHNICAL"),
                body.getOrDefault("direction", "LONG"),
                body.getOrDefault("strength", 0.5),
                body.getOrDefault("metadata", "{}").toString());
        return ApiResponse.ok("Signal created");
    }
}
