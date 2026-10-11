package aegis.watchlist;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface WatchlistRepository extends JpaRepository<WatchlistEntry, String> {
    List<WatchlistEntry> findAllByOrderByAddedAtDesc();
}
