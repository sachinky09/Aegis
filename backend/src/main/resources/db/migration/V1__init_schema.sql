-- Instruments & point-in-time universe
CREATE TABLE IF NOT EXISTS instruments (
    symbol          VARCHAR(32) PRIMARY KEY,
    name            VARCHAR(256) NOT NULL,
    exchange        VARCHAR(16) DEFAULT 'NSE',
    sector          VARCHAR(128),
    is_active       BOOLEAN DEFAULT TRUE,
    listed_at       DATE,
    delisted_at     DATE,
    lot_size        INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS index_membership (
    id              BIGSERIAL PRIMARY KEY,
    index_name      VARCHAR(64) NOT NULL,
    symbol          VARCHAR(32) NOT NULL REFERENCES instruments(symbol),
    effective_from  DATE NOT NULL,
    effective_to    DATE,
    UNIQUE (index_name, symbol, effective_from)
);

CREATE TABLE IF NOT EXISTS corporate_actions (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(32) NOT NULL REFERENCES instruments(symbol),
    action_type     VARCHAR(32) NOT NULL,
    ex_date         DATE NOT NULL,
    ratio           NUMERIC(18,8),
    amount          NUMERIC(18,4),
    notes           TEXT
);

-- Timescale hypertables (created as regular tables first; Timescale extension enabled at runtime if available)
CREATE TABLE IF NOT EXISTS market_ticks (
    time            TIMESTAMPTZ NOT NULL,
    symbol          VARCHAR(32) NOT NULL,
    price           NUMERIC(18,4) NOT NULL,
    volume          BIGINT DEFAULT 0,
    bid             NUMERIC(18,4),
    ask             NUMERIC(18,4),
    PRIMARY KEY (time, symbol)
);

CREATE TABLE IF NOT EXISTS candles (
    time            TIMESTAMPTZ NOT NULL,
    symbol          VARCHAR(32) NOT NULL,
    timeframe       VARCHAR(8) NOT NULL,
    open            NUMERIC(18,4) NOT NULL,
    high            NUMERIC(18,4) NOT NULL,
    low             NUMERIC(18,4) NOT NULL,
    close           NUMERIC(18,4) NOT NULL,
    volume          BIGINT DEFAULT 0,
    PRIMARY KEY (time, symbol, timeframe)
);

CREATE TABLE IF NOT EXISTS technical_features (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(32) NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL,
    features        JSONB NOT NULL,
    UNIQUE (symbol, computed_at)
);

CREATE TABLE IF NOT EXISTS market_regimes (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(32),
    detected_at     TIMESTAMPTZ NOT NULL,
    regime          VARCHAR(32) NOT NULL,
    confidence      NUMERIC(6,4),
    metadata        JSONB
);

CREATE TABLE IF NOT EXISTS news_articles (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(32),
    title           TEXT NOT NULL,
    summary         TEXT,
    source          VARCHAR(128),
    published_at    TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ DEFAULT NOW(),
    sentiment       NUMERIC(6,4),
    raw             JSONB
);

CREATE TABLE IF NOT EXISTS news_archive (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(32),
    title           TEXT NOT NULL,
    summary         TEXT,
    source          VARCHAR(128),
    published_at    TIMESTAMPTZ NOT NULL,
    archived_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    content_hash    VARCHAR(64),
    UNIQUE (symbol, content_hash)
);

CREATE TABLE IF NOT EXISTS model_versions (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    version         VARCHAR(32) NOT NULL,
    algorithm       VARCHAR(64),
    metrics         JSONB,
    is_promoted     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS model_predictions (
    id              BIGSERIAL PRIMARY KEY,
    model_version_id BIGINT REFERENCES model_versions(id),
    symbol          VARCHAR(32) NOT NULL,
    predicted_at    TIMESTAMPTZ NOT NULL,
    target          VARCHAR(32),
    prediction      NUMERIC(18,8),
    probability     NUMERIC(8,6),
    features_used   JSONB
);

CREATE TABLE IF NOT EXISTS signals (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(32) NOT NULL,
    signal_type     VARCHAR(32) NOT NULL,
    direction       VARCHAR(8) NOT NULL,
    strength        NUMERIC(6,4),
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    metadata        JSONB,
    status          VARCHAR(16) DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS signal_outcomes (
    id              BIGSERIAL PRIMARY KEY,
    signal_id       BIGINT REFERENCES signals(id),
    evaluated_at    TIMESTAMPTZ,
    outcome         VARCHAR(16),
    pnl             NUMERIC(18,4)
);

CREATE TABLE IF NOT EXISTS backtests (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    config          JSONB NOT NULL,
    metrics         JSONB,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    status          VARCHAR(16) DEFAULT 'RUNNING'
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id              BIGSERIAL PRIMARY KEY,
    backtest_id     BIGINT REFERENCES backtests(id),
    symbol          VARCHAR(32),
    side            VARCHAR(8),
    entry_time      TIMESTAMPTZ,
    exit_time       TIMESTAMPTZ,
    entry_price     NUMERIC(18,4),
    exit_price      NUMERIC(18,4),
    quantity        INTEGER,
    pnl             NUMERIC(18,4),
    costs           NUMERIC(18,4)
);

CREATE TABLE IF NOT EXISTS paper_accounts (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(64) NOT NULL DEFAULT 'default',
    cash            NUMERIC(18,4) NOT NULL DEFAULT 1000000.00,
    equity          NUMERIC(18,4) NOT NULL DEFAULT 1000000.00,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS paper_orders (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES paper_accounts(id),
    symbol          VARCHAR(32) NOT NULL,
    side            VARCHAR(8) NOT NULL,
    order_type      VARCHAR(16) NOT NULL,
    quantity        INTEGER NOT NULL,
    limit_price     NUMERIC(18,4),
    stop_price      NUMERIC(18,4),
    filled_qty      INTEGER DEFAULT 0,
    avg_fill_price  NUMERIC(18,4),
    status          VARCHAR(16) DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS paper_positions (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES paper_accounts(id),
    symbol          VARCHAR(32) NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 0,
    avg_cost        NUMERIC(18,4) NOT NULL DEFAULT 0,
    market_value    NUMERIC(18,4),
    unrealized_pnl  NUMERIC(18,4),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (account_id, symbol)
);

CREATE TABLE IF NOT EXISTS paper_pnl (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES paper_accounts(id),
    date            DATE NOT NULL,
    realized_pnl    NUMERIC(18,4) DEFAULT 0,
    unrealized_pnl  NUMERIC(18,4) DEFAULT 0,
    equity          NUMERIC(18,4),
    UNIQUE (account_id, date)
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES paper_accounts(id),
    snapshot_at     TIMESTAMPTZ DEFAULT NOW(),
    holdings        JSONB,
    metrics         JSONB
);

CREATE TABLE IF NOT EXISTS risk_metrics (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES paper_accounts(id),
    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    sharpe          NUMERIC(10,4),
    sortino         NUMERIC(10,4),
    calmar          NUMERIC(10,4),
    max_drawdown    NUMERIC(10,6),
    var_95          NUMERIC(18,4),
    cvar_95         NUMERIC(18,4)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    event_type      VARCHAR(64) NOT NULL,
    entity          VARCHAR(64),
    entity_id       VARCHAR(64),
    payload         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default paper account
INSERT INTO paper_accounts (name, cash, equity)
VALUES ('default', 1000000.00, 1000000.00)
ON CONFLICT DO NOTHING;

-- Seed a few instruments
INSERT INTO instruments (symbol, name, exchange, sector, lot_size) VALUES
('RELIANCE', 'Reliance Industries Ltd', 'NSE', 'Energy', 250),
('TCS', 'Tata Consultancy Services', 'NSE', 'IT', 150),
('INFY', 'Infosys Ltd', 'NSE', 'IT', 300),
('HDFCBANK', 'HDFC Bank Ltd', 'NSE', 'Banking', 550),
('ICICIBANK', 'ICICI Bank Ltd', 'NSE', 'Banking', 700),
('SBIN', 'State Bank of India', 'NSE', 'Banking', 750),
('BHARTIARTL', 'Bharti Airtel Ltd', 'NSE', 'Telecom', 475),
('ITC', 'ITC Ltd', 'NSE', 'FMCG', 1600),
('LT', 'Larsen & Toubro Ltd', 'NSE', 'Infrastructure', 150),
('AXISBANK', 'Axis Bank Ltd', 'NSE', 'Banking', 625)
ON CONFLICT (symbol) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON market_ticks (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_candles_symbol_tf ON candles (symbol, timeframe, time DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals (symbol, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_archive_symbol ON news_archive (symbol, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_index_membership ON index_membership (index_name, effective_from, effective_to);
