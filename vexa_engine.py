"""VEXA Intelligence Engine v1.

Historical, reference-price analysis for medium-term currency/asset allocation.
This module generates decision support, not guaranteed forecasts or executable quotes.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import requests

ASSET_IDS = {
    "USDC": "usd-coin",
    "USDT": "tether",
    "BTC": "bitcoin",
    "ETH": "ethereum",
}
FIAT = ("BRL", "EUR", "GBP")
USER_AGENT = "VEXA-Intelligence/1.0"


def _request_json(url: str, params: Optional[dict] = None) -> dict:
    response = requests.get(
        url,
        params=params,
        timeout=15,
        headers={"accept": "application/json", "user-agent": USER_AGENT},
    )
    response.raise_for_status()
    return response.json()


def fetch_historical_prices(days: int = 120) -> Tuple[pd.DataFrame, list, list]:
    """Return daily USD prices for supported assets, source labels and errors."""
    end = date.today()
    start = end - timedelta(days=days)
    series = {}
    sources = []
    errors = []

    # Fiat reference rates: Frankfurter reports units of foreign currency per USD.
    try:
        payload = _request_json(
            f"https://api.frankfurter.app/{start.isoformat()}..{end.isoformat()}",
            {"from": "USD", "to": ",".join(FIAT)},
        )
        rows = payload.get("rates", {})
        fiat_frame = pd.DataFrame.from_dict(rows, orient="index").sort_index()
        if not fiat_frame.empty:
            fiat_frame.index = pd.to_datetime(fiat_frame.index)
            for symbol in FIAT:
                if symbol in fiat_frame:
                    # Convert quote units per USD into USD value per one quote unit.
                    series[symbol] = (1.0 / pd.to_numeric(fiat_frame[symbol], errors="coerce")).dropna()
            sources.append("Frankfurter — histórico cambial de referência")
    except Exception as exc:
        errors.append(f"Moedas fiduciárias (Frankfurter): {exc}")

    # Crypto reference prices: CoinGecko public market chart endpoint.
    for symbol, coin_id in ASSET_IDS.items():
        try:
            payload = _request_json(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                {"vs_currency": "usd", "days": str(days), "interval": "daily"},
            )
            points = payload.get("prices", [])
            if points:
                frame = pd.DataFrame(points, columns=["timestamp", "price"])
                frame["date"] = pd.to_datetime(frame["timestamp"], unit="ms").dt.normalize()
                values = frame.groupby("date")["price"].last().astype(float)
                series[symbol] = values[values > 0]
        except Exception as exc:
            errors.append(f"{symbol} (CoinGecko): {exc}")

    # USD is the numeraire. Forward-fill fiat weekends and align all series.
    # USD is the numeraire. It also provides a transparent peg proxy for
    # stablecoins if their individual market-history endpoint is unavailable.
    daily_index = pd.date_range(
        start=pd.Timestamp(start), end=pd.Timestamp(end), freq="D"
    )
    series["USD"] = pd.Series(1.0, index=daily_index)

    # Stablecoins target USD. When CoinGecko history is missing/rate-limited,
    # use USD as an explicit peg proxy rather than failing the whole analysis.
    # The UI/source note makes this assumption visible to the user.
    for stablecoin in ("USDC", "USDT"):
        if stablecoin not in series or series[stablecoin].dropna().shape[0] < 60:
            series[stablecoin] = pd.Series(1.0, index=daily_index)
            sources.append(
                f"{stablecoin} — proxy de paridade USD (histórico próprio indisponível)"
            )

    if not series:
        return pd.DataFrame(), sources, errors

    prices = pd.concat(series, axis=1).sort_index()
    prices = prices[~prices.index.duplicated(keep="last")]
    prices = prices.resample("D").last().ffill(limit=4)
    prices = prices.replace([np.inf, -np.inf], np.nan)
    return prices, sources, errors


def _clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(np.clip(value, low, high))


def _asset_metrics(prices: pd.Series, origin: pd.Series, cost_pct: Optional[float]) -> dict:
    data = pd.concat(
        [prices.rename("asset"), origin.rename("origin")], axis=1
    ).dropna()
    if len(data) < 60:
        raise ValueError("Histórico insuficiente: são necessários pelo menos 60 pontos diários.")

    asset = data["asset"].astype(float)
    base = data["origin"].astype(float)
    ret30 = float(asset.iloc[-1] / asset.iloc[-31] - 1.0)
    ret90 = float(asset.iloc[-1] / asset.iloc[-min(91, len(asset))] - 1.0)
    base30 = float(base.iloc[-1] / base.iloc[-31] - 1.0)
    base90 = float(base.iloc[-1] / base.iloc[-min(91, len(base))] - 1.0)
    rel30 = ret30 - base30
    rel90 = ret90 - base90

    sma20 = float(asset.tail(20).mean())
    sma50 = float(asset.tail(50).mean())
    sma100 = float(asset.tail(100).mean()) if len(asset) >= 100 else float(asset.mean())
    trend_score = 50.0 + (25.0 if sma20 > sma50 else 0.0) + (25.0 if sma50 > sma100 else 0.0)

    rolling = asset.tail(min(90, len(asset)))
    mean90 = float(rolling.mean())
    std90 = float(rolling.std(ddof=0))
    zscore = (float(asset.iloc[-1]) - mean90) / std90 if std90 > 0 else 0.0
    valuation_score = _clip(50.0 - zscore * 8.0)

    daily_returns = asset.pct_change().dropna().tail(30)
    annualized_vol = float(daily_returns.std(ddof=1) * np.sqrt(365)) if len(daily_returns) > 2 else 0.0
    risk_score = _clip(100.0 - annualized_vol * 60.0)

    relative_momentum = 0.60 * rel30 + 0.40 * rel90
    momentum_score = _clip(50.0 + relative_momentum * 300.0)

    # Missing route-cost data is neutral, not treated as free.
    if cost_pct is None:
        cost_score = 50.0
    else:
        cost_score = _clip(100.0 - max(0.0, float(cost_pct)) * 100.0)

    score = (
        momentum_score * 0.25
        + trend_score * 0.25
        + valuation_score * 0.15
        + risk_score * 0.25
        + cost_score * 0.10
    )
    return {
        "score": round(score, 1),
        "momentum_score": round(momentum_score, 1),
        "trend_score": round(trend_score, 1),
        "valuation_score": round(valuation_score, 1),
        "risk_score": round(risk_score, 1),
        "cost_score": round(cost_score, 1),
        "return_30d": ret30,
        "return_90d": ret90,
        "relative_30d": rel30,
        "relative_90d": rel90,
        "relative_momentum": relative_momentum,
        "annualized_volatility": annualized_vol,
        "zscore_90d": zscore,
    }


def analyze_portfolio(
    origin_symbol: str,
    prices: pd.DataFrame,
    cost_percentages: Optional[Dict[str, float]] = None,
    risk_profile: str = "Moderado",
) -> dict:
    """Score assets against the user's current holding and issue a cautious action."""
    if origin_symbol not in prices.columns or prices[origin_symbol].dropna().empty:
        raise ValueError(f"Não há histórico suficiente para {origin_symbol}.")

    origin = prices[origin_symbol].dropna()
    costs = cost_percentages or {}
    metrics = {}
    for symbol in prices.columns:
        if symbol == origin_symbol:
            continue
        try:
            metrics[symbol] = _asset_metrics(
                prices[symbol].dropna(),
                origin,
                costs.get(symbol),
            )
        except (ValueError, IndexError, ZeroDivisionError):
            continue

    if not metrics:
        raise ValueError("Não há ativos com histórico suficiente para comparação.")

    origin_metrics = _asset_metrics(origin, origin, costs.get(origin_symbol))
    candidates = sorted(metrics.items(), key=lambda item: item[1]["score"], reverse=True)
    best_symbol, best = candidates[0]
    score_gap = best["score"] - origin_metrics["score"]

    # These are conservative research thresholds, not calibrated return forecasts.
    min_edge = {"Conservador": 0.04, "Moderado": 0.025, "Arrojado": 0.015}.get(
        risk_profile, 0.025
    )
    relative_signal = best["relative_momentum"]
    if score_gap >= 25 and relative_signal >= 0.08 and best["risk_score"] >= 45:
        action = "Converter"
        rationale = "Sinal relativo forte, persistente e com risco dentro do limite inicial."
    elif score_gap >= 12 and relative_signal >= min_edge and best["risk_score"] >= 35:
        action = "Converter parcialmente"
        rationale = "Há vantagem relativa suficiente para avaliar uma exposição parcial."
    else:
        action = "Manter"
        rationale = "A vantagem relativa ainda não supera os limites de decisão do perfil selecionado."

    return {
        "origin": origin_symbol,
        "origin_score": origin_metrics["score"],
        "recommendation": action,
        "candidate": best_symbol if action != "Manter" else None,
        "candidate_score": best["score"],
        "score_gap": round(score_gap, 1),
        "relative_momentum": relative_signal,
        "rationale": rationale,
        "risk_profile": risk_profile,
        "assets": metrics,
        "history_start": str(prices.dropna(how="all").index.min().date()),
        "history_end": str(prices.dropna(how="all").index.max().date()),
        "methodology": "Score composto: momentum 25%, tendência 25%, desvio histórico 15%, risco 25%, custos 10%.",
    }
