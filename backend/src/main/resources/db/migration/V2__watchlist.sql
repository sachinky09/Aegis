-- Personal watchlist (single user)
CREATE TABLE IF NOT EXISTS watchlist (
    symbol      VARCHAR(32) PRIMARY KEY REFERENCES instruments(symbol) ON DELETE CASCADE,
    notes       TEXT,
    added_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default watchlist from existing instruments
INSERT INTO watchlist (symbol)
SELECT symbol FROM instruments WHERE is_active = TRUE
ON CONFLICT (symbol) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_watchlist_added ON watchlist (added_at DESC);
