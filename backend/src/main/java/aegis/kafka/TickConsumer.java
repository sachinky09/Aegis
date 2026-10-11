package aegis.kafka;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.time.Duration;

@Component
@ConditionalOnProperty(name = "aegis.kafka.enabled", havingValue = "true")
public class TickConsumer {

    private static final Logger log = LoggerFactory.getLogger(TickConsumer.class);

    private final StringRedisTemplate redis;
    private final JdbcTemplate jdbc;

    public TickConsumer(StringRedisTemplate redis, JdbcTemplate jdbc) {
        this.redis = redis;
        this.jdbc = jdbc;
    }

    @KafkaListener(topics = "market.tick", groupId = "feature-engine")
    public void consume(ConsumerRecord<String, String> record) {
        try {
            String dedupeKey = "dedupe:tick:" + record.key() + ":" + record.timestamp();
            Boolean isNew = redis.opsForValue().setIfAbsent(dedupeKey, "1", Duration.ofMinutes(10));
            if (Boolean.FALSE.equals(isNew)) {
                log.debug("Skipping duplicate tick {}", dedupeKey);
                return;
            }
            log.debug("Processing tick: key={}, value={}", record.key(), record.value());
        } catch (Exception e) {
            log.error("Error processing tick", e);
        }
    }

    @KafkaListener(topics = "market.tick", groupId = "persistence")
    public void persist(ConsumerRecord<String, String> record) {
        try {
            String key = record.key() != null ? record.key() : "UNKNOWN";
            log.debug("Persist consumer saw tick for {}", key);
        } catch (Exception e) {
            log.error("Persist error", e);
        }
    }
}
