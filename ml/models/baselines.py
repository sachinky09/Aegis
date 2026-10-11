"""ML baselines: logistic, GBM, OOF stack, SHAP, HMM regimes, LSTM, GARCH."""
from __future__ import annotations

from typing import Any

import numpy as np


def train_direction_baseline(X: np.ndarray, y: np.ndarray) -> dict:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import accuracy_score

    if len(X) < 30:
        return {"error": "insufficient samples", "n": len(X)}

    tscv = TimeSeriesSplit(n_splits=3)
    scores = []
    for train_idx, test_idx in tscv.split(X):
        if len(train_idx) > 5:
            train_idx = train_idx[:-2]
        if len(test_idx) > 5:
            test_idx = test_idx[2:]
        if len(train_idx) < 10 or len(test_idx) < 5:
            continue
        clf = LogisticRegression(max_iter=500)
        clf.fit(X[train_idx], y[train_idx])
        pred = clf.predict(X[test_idx])
        scores.append(accuracy_score(y[test_idx], pred))

    final = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
    final.fit(X, y)
    proba = final.predict_proba(X[-1:].reshape(1, -1))[0]
    return {
        "cv_accuracy_mean": float(np.mean(scores)) if scores else None,
        "cv_folds": len(scores),
        "latest_proba_up": float(proba[1]) if len(proba) > 1 else float(proba[0]),
        "model": "GradientBoostingClassifier",
    }


def oof_stack(X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """Out-of-fold stacking: logistic + GBM → meta logistic."""
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import accuracy_score

    if len(X) < 40:
        return {"error": "insufficient samples for OOF", "n": len(X)}
    tscv = TimeSeriesSplit(n_splits=4)
    oof = np.zeros((len(X), 2))
    for tr, te in tscv.split(X):
        lr = LogisticRegression(max_iter=400)
        gb = GradientBoostingClassifier(n_estimators=40, max_depth=2, random_state=42)
        lr.fit(X[tr], y[tr])
        gb.fit(X[tr], y[tr])
        oof[te, 0] = lr.predict_proba(X[te])[:, 1]
        oof[te, 1] = gb.predict_proba(X[te])[:, 1]
    meta = LogisticRegression(max_iter=400)
    # fit meta on rows that got OOF fills
    mask = oof.sum(axis=1) > 0
    meta.fit(oof[mask], y[mask])
    pred = meta.predict(oof[mask])
    return {
        "model": "OOF_stack_logistic_gbm_meta",
        "oof_accuracy": float(accuracy_score(y[mask], pred)),
        "n_oof": int(mask.sum()),
        "meta_coef": meta.coef_.ravel().tolist(),
    }


def shap_importance(X: np.ndarray, y: np.ndarray, feature_names: list[str] | None = None) -> dict[str, Any]:
    from sklearn.ensemble import GradientBoostingClassifier
    names = feature_names or [f"f{i}" for i in range(X.shape[1])]
    clf = GradientBoostingClassifier(n_estimators=40, max_depth=2, random_state=42)
    clf.fit(X, y)
    try:
        import shap
        explainer = shap.TreeExplainer(clf)
        sv = explainer.shap_values(X[-50:])
        if isinstance(sv, list):
            sv = sv[1]
        mean_abs = np.mean(np.abs(sv), axis=0)
        ranking = sorted(
            [{"feature": names[i], "mean_abs_shap": float(mean_abs[i])} for i in range(len(names))],
            key=lambda d: d["mean_abs_shap"],
            reverse=True,
        )
        return {"method": "shap_tree", "ranking": ranking}
    except Exception as e:
        imp = clf.feature_importances_
        ranking = sorted(
            [{"feature": names[i], "importance": float(imp[i])} for i in range(len(names))],
            key=lambda d: d["importance"],
            reverse=True,
        )
        return {"method": "gbm_importance_fallback", "ranking": ranking, "note": str(e)}


def hmm_regimes(returns: np.ndarray, n_states: int = 3) -> dict[str, Any]:
    """Gaussian HMM regimes via hmmlearn; fallback to quantile regimes."""
    r = np.asarray(returns, dtype=float).reshape(-1, 1)
    if len(r) < 30:
        return {"error": "insufficient returns", "n": len(r)}
    try:
        from hmmlearn.hmm import GaussianHMM
        model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100, random_state=42)
        model.fit(r)
        states = model.predict(r)
        return {
            "model": "GaussianHMM",
            "n_states": n_states,
            "last_state": int(states[-1]),
            "state_means": model.means_.ravel().tolist(),
            "recent_states": states[-10:].tolist(),
        }
    except Exception as e:
        q = np.quantile(r.ravel(), [0.33, 0.66])
        states = np.digitize(r.ravel(), q)
        return {
            "model": "quantile_regimes_fallback",
            "n_states": 3,
            "last_state": int(states[-1]),
            "thresholds": q.tolist(),
            "note": str(e),
        }


def lstm_direction(X: np.ndarray, y: np.ndarray, seq_len: int = 10) -> dict[str, Any]:
    """
    Sequence model for direction.
    Tries PyTorch LSTM if available; else sklearn MLP on flattened windows.
    """
    if len(X) < seq_len + 20:
        return {"error": "insufficient samples for sequence model", "n": len(X)}
    # build sequences
    xs, ys = [], []
    for i in range(seq_len, len(X)):
        xs.append(X[i - seq_len : i].ravel())
        ys.append(y[i])
    Xs = np.asarray(xs)
    ys = np.asarray(ys)
    split = int(len(Xs) * 0.7)
    try:
        import torch
        import torch.nn as nn

        class TinyLSTM(nn.Module):
            def __init__(self, n_feat, hidden=16):
                super().__init__()
                self.lstm = nn.LSTM(n_feat, hidden, batch_first=True)
                self.fc = nn.Linear(hidden, 2)

            def forward(self, x):
                # x: (B, T*F) -> (B, T, F)
                b = x.shape[0]
                x = x.view(b, seq_len, -1)
                out, _ = self.lstm(x)
                return self.fc(out[:, -1, :])

        n_feat = X.shape[1]
        model = TinyLSTM(n_feat)
        opt = torch.optim.Adam(model.parameters(), lr=1e-2)
        loss_fn = nn.CrossEntropyLoss()
        xt = torch.tensor(Xs[:split], dtype=torch.float32)
        yt = torch.tensor(ys[:split], dtype=torch.long)
        model.train()
        for _ in range(25):
            opt.zero_grad()
            logits = model(xt)
            loss = loss_fn(logits, yt)
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            pred = model(torch.tensor(Xs[split:], dtype=torch.float32)).argmax(1).numpy()
        acc = float((pred == ys[split:]).mean()) if len(ys[split:]) else None
        return {"model": "pytorch_lstm", "test_accuracy": acc, "seq_len": seq_len}
    except Exception as e:
        from sklearn.neural_network import MLPClassifier
        from sklearn.metrics import accuracy_score
        clf = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=200, random_state=42)
        clf.fit(Xs[:split], ys[:split])
        pred = clf.predict(Xs[split:])
        return {
            "model": "mlp_sequence_fallback",
            "test_accuracy": float(accuracy_score(ys[split:], pred)),
            "seq_len": seq_len,
            "note": str(e),
        }


def ewma_vol(returns: np.ndarray, lam: float = 0.94) -> float:
    if len(returns) == 0:
        return 0.0
    var = returns[0] ** 2
    for r in returns[1:]:
        var = lam * var + (1 - lam) * r ** 2
    return float(np.sqrt(var))


def garch_vol(returns: np.ndarray) -> dict:
    try:
        from arch import arch_model
        am = arch_model(returns * 100, vol="Garch", p=1, q=1, rescale=False)
        res = am.fit(disp="off")
        forecast = res.forecast(horizon=1)
        vol = float(np.sqrt(forecast.variance.values[-1, 0]) / 100)
        return {"method": "GARCH(1,1)", "vol": vol, "aic": float(res.aic)}
    except Exception as e:
        return {"method": "EWMA", "vol": ewma_vol(returns), "note": str(e)}
