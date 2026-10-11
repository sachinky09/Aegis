package aegis.market;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final TickWebSocketHandler tickHandler;

    public WebSocketConfig(TickWebSocketHandler tickHandler) {
        this.tickHandler = tickHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(tickHandler, "/ws/ticks").setAllowedOrigins("*");
    }
}
