package aegis.portfolio;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface PaperOrderRepository extends JpaRepository<PaperOrder, Long> {
    List<PaperOrder> findByAccountIdOrderByCreatedAtDesc(Long accountId);
}
