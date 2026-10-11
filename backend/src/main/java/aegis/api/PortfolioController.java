package aegis.api;

import aegis.common.ApiResponse;
import aegis.portfolio.PaperTradingService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/portfolio")
public class PortfolioController {

    private final PaperTradingService service;

    public PortfolioController(PaperTradingService service) {
        this.service = service;
    }

    @GetMapping("/summary")
    public ApiResponse<Map<String, Object>> summary() {
        return ApiResponse.ok(service.getSummary());
    }
}
