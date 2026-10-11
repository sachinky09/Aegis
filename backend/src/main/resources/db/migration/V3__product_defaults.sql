-- Empty personal watchlist by default (remove any seed rows)
DELETE FROM watchlist;

-- Unlimited paper cash (soft marker: very large balance; service also skips cash cap)
UPDATE paper_accounts SET cash = 999999999999.00, equity = 999999999999.00 WHERE id = 1;
