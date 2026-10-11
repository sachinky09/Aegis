package aegis.common;

import jakarta.persistence.*;
import java.time.LocalDate;
import java.time.Instant;

@Entity
@Table(name = "instruments")
public class Instrument {
    @Id
    private String symbol;
    private String name;
    private String exchange;
    private String sector;
    @Column(name = "is_active")
    private Boolean isActive = true;
    @Column(name = "listed_at")
    private LocalDate listedAt;
    @Column(name = "delisted_at")
    private LocalDate delistedAt;
    @Column(name = "lot_size")
    private Integer lotSize = 1;
    @Column(name = "created_at")
    private Instant createdAt;

    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getExchange() { return exchange; }
    public void setExchange(String exchange) { this.exchange = exchange; }
    public String getSector() { return sector; }
    public void setSector(String sector) { this.sector = sector; }
    public Boolean getIsActive() { return isActive; }
    public void setIsActive(Boolean isActive) { this.isActive = isActive; }
    public LocalDate getListedAt() { return listedAt; }
    public void setListedAt(LocalDate listedAt) { this.listedAt = listedAt; }
    public LocalDate getDelistedAt() { return delistedAt; }
    public void setDelistedAt(LocalDate delistedAt) { this.delistedAt = delistedAt; }
    public Integer getLotSize() { return lotSize; }
    public void setLotSize(Integer lotSize) { this.lotSize = lotSize; }
    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
