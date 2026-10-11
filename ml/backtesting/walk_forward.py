"""Walk-forward validation with purge + embargo."""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass


@dataclass
class FoldResult:
    fold: int
    train_size: int
    test_size: int
    accuracy: float
    sharpe: float


def purge_embargo_indices(
    n: int,
    train_end: int,
    test_start: int,
    test_end: int,
    embargo: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Remove train samples that overlap label horizon (purge) and
    apply embargo gap after train before test.
    """
    # purge: drop last `embargo` samples from train that could leak into test labels
    train_idx = np.arange(0, max(0, train_end - embargo))
    test_idx = np.arange(test_start, test_end)
    return train_idx, test_idx


def walk_forward(
    X: np.ndarray,
    y: np.ndarray,
    returns: np.ndarray | None = None,
    n_splits: int = 5,
    embargo: int = 5,
) -> dict:
    n = len(X)
    if n < 50:
        return {"error": "need >= 50 samples", "n": n}

    fold_size = n // (n_splits + 1)
    results: list[FoldResult] = []

    for i in range(n_splits):
        train_end = fold_size * (i + 1)
        test_start = train_end + embargo
        test_end = min(test_start + fold_size, n)
        if test_start >= n or train_end < 20:
            continue

        train_idx, test_idx = purge_embargo_indices(n, train_end, test_start, test_end, embargo)
        if len(train_idx) < 15 or len(test_idx) < 5:
            continue

        # Simple logistic-style: use mean of positive features as score
        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]

        # Fit crude linear weights
        w = np.linalg.lstsq(X_train, y_train.astype(float), rcond=None)[0]
        pred_score = X_test @ w
        pred = (pred_score > 0.5).astype(int)
        acc = float(np.mean(pred == y_test))

        if returns is not None:
            r = returns[test_idx]
            # long when pred==1
            strat = np.where(pred == 1, r, -r)
            sharpe = float(np.mean(strat) / (np.std(strat) + 1e-9) * np.sqrt(252))
        else:
            sharpe = 0.0

        results.append(FoldResult(i, len(train_idx), len(test_idx), acc, sharpe))

    if not results:
        return {"error": "no valid folds"}

    return {
        "n_folds": len(results),
        "mean_accuracy": float(np.mean([r.accuracy for r in results])),
        "mean_sharpe": float(np.mean([r.sharpe for r in results])),
        "folds": [
            {
                "fold": r.fold,
                "train_size": r.train_size,
                "test_size": r.test_size,
                "accuracy": r.accuracy,
                "sharpe": r.sharpe,
            }
            for r in results
        ],
        "embargo": embargo,
        "purge": True,
    }


def probability_of_backtest_overfitting(is_sharpes: list[float], oos_sharpes: list[float]) -> float:
    """Simplified PBO: fraction of trials where OOS sharpe rank is worse than median IS."""
    if not is_sharpes or not oos_sharpes:
        return 0.5
    # Rank correlation style proxy
    is_med = float(np.median(is_sharpes))
    worse = sum(1 for o in oos_sharpes if o < is_med)
    return float(worse / len(oos_sharpes))
