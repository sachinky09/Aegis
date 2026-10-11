package aegis.api;

import aegis.common.ApiResponse;
import aegis.common.Instrument;
import aegis.common.InstrumentRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/instruments")
public class InstrumentController {

    private final InstrumentRepository repo;

    public InstrumentController(InstrumentRepository repo) {
        this.repo = repo;
    }

    @GetMapping
    public ApiResponse<List<Instrument>> list() {
        return ApiResponse.ok(repo.findByIsActiveTrue());
    }

    @GetMapping("/{symbol}")
    public ApiResponse<Instrument> get(@PathVariable String symbol) {
        return repo.findById(symbol)
                .map(ApiResponse::ok)
                .orElse(ApiResponse.error("Instrument not found"));
    }
}
