package aegis.kafka;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
@ConditionalOnProperty(name = "aegis.kafka.enabled", havingValue = "true")
public class KafkaConfig {

    @Bean
    public NewTopic marketTickTopic() {
        return TopicBuilder.name("market.tick").partitions(3).replicas(1).build();
    }

    @Bean
    public NewTopic marketCandleTopic() {
        return TopicBuilder.name("market.candle").partitions(3).replicas(1).build();
    }

    @Bean
    public NewTopic newsTriggerTopic() {
        return TopicBuilder.name("news.trigger").partitions(1).replicas(1).build();
    }

    @Bean
    public NewTopic newsTriggerDlq() {
        return TopicBuilder.name("news.trigger.dlq").partitions(1).replicas(1).build();
    }

    @Bean
    public NewTopic newsAnalyzedTopic() {
        return TopicBuilder.name("news.analyzed").partitions(1).replicas(1).build();
    }

    @Bean
    public NewTopic mlPredictionTopic() {
        return TopicBuilder.name("ml.prediction").partitions(2).replicas(1).build();
    }

    @Bean
    public NewTopic signalGeneratedTopic() {
        return TopicBuilder.name("signal.generated").partitions(2).replicas(1).build();
    }

    @Bean
    public NewTopic riskAlertTopic() {
        return TopicBuilder.name("risk.alert").partitions(1).replicas(1).build();
    }

    @Bean
    public NewTopic auditEventTopic() {
        return TopicBuilder.name("audit.event").partitions(1).replicas(1).build();
    }
}
