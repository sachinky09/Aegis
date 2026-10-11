package aegis.portfolio;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface PaperAccountRepository extends JpaRepository<PaperAccount, Long> {
    Optional<PaperAccount> findByName(String name);
}
