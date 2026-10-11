package aegis.portfolio;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface PaperPositionRepository extends JpaRepository<PaperPosition, Long> {
    List<PaperPosition> findByAccountId(Long accountId);
    Optional<PaperPosition> findByAccountIdAndSymbol(Long accountId, String symbol);
}
