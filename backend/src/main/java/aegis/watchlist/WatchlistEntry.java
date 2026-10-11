package aegis.watchlist;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "watchlist")
public class WatchlistEntry {
    @Id
    private String symbol;
    private String notes;
    @Column(name = "added_at")
    private Instant addedAt;

    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }
    public Instant getAddedAt() { return addedAt; }
    public void setAddedAt(Instant addedAt) { this.addedAt = addedAt; }
}
