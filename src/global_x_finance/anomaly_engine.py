from __future__ import annotations

import json
import math
import statistics
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


NORMAL_QUALITY = {"COMPLETE", "PARTIAL_PRICE_HISTORY", "PARTIAL_40D_RANGE"}
RULE_NAMES = (
    "VOLUME_SPIKE",
    "RANGE_BREAKOUT_20D",
    "RANGE_BREAKOUT_40D",
    "PRICE_VOLUME_BREAKOUT",
    "QUIET_TO_VOLUME_SPIKE",
    "PRICE_ANOMALY",
)
LIQUIDITY_LOW_MAX_PERCENTILE = 25.0
LIQUIDITY_HIGH_MIN_PERCENTILE = 75.0


@dataclass(frozen=True)
class AnomalyRuleConfig:
    version: str
    minimum_prior_sessions: int
    volume_baseline_sessions: int
    volume_spike_ratio: float
    range_breakout_sessions: tuple[int, int]
    quiet_recent_sessions: int
    quiet_recent_to_normal_max: float
    quiet_current_to_normal_min: float
    quiet_current_to_recent_min: float
    price_return_sessions: int
    price_anomaly_abs_zscore: float
    extreme_prior_return_abs_pct: float
    raw: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path) -> "AnomalyRuleConfig":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            version=str(raw["version"]),
            minimum_prior_sessions=int(raw["minimum_prior_sessions"]),
            volume_baseline_sessions=int(raw["volume_baseline_sessions"]),
            volume_spike_ratio=float(raw["volume_spike_ratio"]),
            range_breakout_sessions=tuple(int(value) for value in raw["range_breakout_sessions"]),
            quiet_recent_sessions=int(raw["quiet_recent_sessions"]),
            quiet_recent_to_normal_max=float(raw["quiet_recent_to_normal_max"]),
            quiet_current_to_normal_min=float(raw["quiet_current_to_normal_min"]),
            quiet_current_to_recent_min=float(raw["quiet_current_to_recent_min"]),
            price_return_sessions=int(raw["price_return_sessions"]),
            price_anomaly_abs_zscore=float(raw["price_anomaly_abs_zscore"]),
            extreme_prior_return_abs_pct=float(raw["extreme_prior_return_abs_pct"]),
            raw=raw,
        )


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _percentile(values: Iterable[float], percentile: float) -> float | None:
    ordered = sorted(value for value in values if math.isfinite(value))
    if not ordered:
        return None
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def complete_replay_dates(
    connection,
    *,
    limit: int,
    minimum_market_coverage: float = 0.8,
) -> list[str]:
    totals = {
        row["exchange_code"]: int(row["count"])
        for row in connection.execute(
            """SELECT exchange_code, COUNT(*) AS count FROM official_securities
               WHERE exchange_code IN ('TWSE','TPEX') GROUP BY exchange_code"""
        )
    }
    dates: list[str] = []
    for row in connection.execute(
        """SELECT trade_date,
                  SUM(CASE WHEN exchange_code='TWSE' THEN 1 ELSE 0 END) AS twse_count,
                  SUM(CASE WHEN exchange_code='TPEX' THEN 1 ELSE 0 END) AS tpex_count
           FROM official_market_data_daily
           WHERE data_status='EOD'
           GROUP BY trade_date ORDER BY trade_date DESC"""
    ):
        if (
            int(row["twse_count"]) >= totals["TWSE"] * minimum_market_coverage
            and int(row["tpex_count"]) >= totals["TPEX"] * minimum_market_coverage
        ):
            dates.append(str(row["trade_date"]))
            if len(dates) >= limit:
                break
    if not dates:
        raise ValueError("No replay date has sufficient TWSE and TPEx EOD coverage")
    return dates


def latest_complete_replay_date(connection, *, minimum_market_coverage: float = 0.8) -> str:
    return complete_replay_dates(
        connection, limit=1, minimum_market_coverage=minimum_market_coverage
    )[0]


class AnomalyEngine:
    """Explainable prior-only daily anomaly replay over unified official MarketData."""

    def __init__(self, connection, config: AnomalyRuleConfig):
        self.connection = connection
        self.config = config

    def replay(self, replay_date: str | None = None) -> dict[str, Any]:
        replay_date = replay_date or latest_complete_replay_date(self.connection)
        results: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        distributions: dict[str, list[float]] = {
            "volume_ratio": [],
            "abs_price_zscore": [],
            "breakout_pct": [],
            "recent5_to_20d_volume_ratio": [],
            "current_to_recent5_volume_ratio": [],
        }
        for security in self.connection.execute(
            """SELECT id, exchange_code, ticker, company_name
               FROM official_securities
               WHERE exchange_code IN ('TWSE','TPEX')
               ORDER BY exchange_code, ticker"""
        ):
            result = self._evaluate_security(dict(security), replay_date)
            if result["data_quality"] in NORMAL_QUALITY:
                results.append(result)
                for key in distributions:
                    value = result["raw_metrics"].get(key)
                    if value is not None:
                        distributions[key].append(float(value))
            else:
                excluded.append(result)

        self._assign_liquidity_context(results)

        results.sort(key=self._ranking_key)
        for rank, result in enumerate(results, start=1):
            result["rank"] = rank

        counts = {rule: sum(rule in row["matched_rules"] for row in results) for rule in RULE_NAMES}
        counts["MULTI_SIGNAL"] = sum(len(row["matched_rules"]) >= 2 for row in results)
        distribution_summary = {
            key: {
                "count": len(values),
                "p50": _percentile(values, 0.50),
                "p90": _percentile(values, 0.90),
                "p95": _percentile(values, 0.95),
                "p975": _percentile(values, 0.975),
                "p99": _percentile(values, 0.99),
                "maximum": max(values) if values else None,
            }
            for key, values in distributions.items()
        }
        market_counts = {
            market: sum(row["market"] == market for row in results) for market in ("TWSE", "TPEX")
        }
        prior_40d_coverage = {
            market: sum(
                row["market"] == market and row["raw_metrics"].get("prior_40d_high") is not None
                for row in results
            )
            for market in ("TWSE", "TPEX")
        }
        excluded_counts = {
            quality: sum(row["data_quality"] == quality for row in excluded)
            for quality in sorted({row["data_quality"] for row in excluded})
        }
        return {
            "rule_version": self.config.version,
            "replay_date": replay_date,
            "participating": market_counts,
            "participating_total": len(results),
            "prior_40d_coverage": prior_40d_coverage,
            "excluded_counts": excluded_counts,
            "rule_counts": counts,
            "distribution": distribution_summary,
            "ranked": results,
            "excluded": excluded,
            "audit_cases": self._audit_cases(results, excluded),
        }

    def _evaluate_security(self, security: dict[str, Any], replay_date: str) -> dict[str, Any]:
        rows = [
            dict(row)
            for row in self.connection.execute(
                """SELECT trade_date, opening_price, highest_price, lowest_price,
                          closing_price, trade_volume, trade_value, data_status
                   FROM official_market_data_daily
                   WHERE security_id=? AND trade_date<=?
                   ORDER BY trade_date""",
                (security["id"], replay_date),
            )
        ]
        current = next(
            (row for row in reversed(rows) if row["trade_date"] == replay_date and row["data_status"] == "EOD"),
            None,
        )
        prior = [row for row in rows if row["trade_date"] < replay_date and row["data_status"] == "EOD"]
        base = {
            "rank": None,
            "security_id": security["id"],
            "name": security["company_name"],
            "market": security["exchange_code"],
            "ticker": security["ticker"],
            "replay_date": replay_date,
            "matched_rules": [],
            "rule_severity": {},
            "raw_metrics": {},
            "why_selected": "",
        }
        if current is None:
            return {**base, "data_quality": "NO_CURRENT_DATA", "why_selected": "Replay日无有效EOD行情，未参与排名。"}
        current_ohlc = [_number(current[key]) for key in ("opening_price", "highest_price", "lowest_price", "closing_price")]
        if any(value is None or value <= 0 for value in current_ohlc) or current["trade_volume"] is None:
            return {**base, "data_quality": "INVALID_CURRENT_DATA", "why_selected": "Replay日OHLCV缺失或非正价格，未参与排名。"}
        if len(prior) < self.config.minimum_prior_sessions:
            return {
                **base,
                "data_quality": "INSUFFICIENT_HISTORY",
                "raw_metrics": {"prior_sessions": len(prior)},
                "why_selected": f"Replay日前仅{len(prior)}个有效交易日，不足20日Baseline。",
            }
        lookback = prior[-max(self.config.range_breakout_sessions) :]
        for row in lookback:
            ohlc = [_number(row[key]) for key in ("opening_price", "highest_price", "lowest_price", "closing_price")]
            if any(value is None or value <= 0 for value in ohlc) or row["trade_volume"] is None:
                return {
                    **base,
                    "data_quality": "EXTREME_OFFICIAL_DATA",
                    "why_selected": "历史窗口含零价、非正价格或缺失OHLCV，未进入正常排名。",
                }

        closes = [float(row["closing_price"]) for row in prior]
        prior_returns = [(closes[index] / closes[index - 1] - 1) * 100 for index in range(1, len(closes))]
        extreme_returns = [value for value in prior_returns[-40:] if abs(value) > self.config.extreme_prior_return_abs_pct]
        if extreme_returns:
            return {
                **base,
                "data_quality": "EXTREME_OFFICIAL_DATA",
                "raw_metrics": {"maximum_prior_abs_return_pct": max(abs(value) for value in extreme_returns)},
                "why_selected": "历史窗口含超过30%的未复权价格跳变，可能涉及除权、减资或拆分，未进入正常排名。",
            }

        current_close = float(current["closing_price"])
        previous_close = closes[-1]
        current_volume = int(current["trade_volume"])
        volume_rows = prior[-self.config.volume_baseline_sessions :]
        baseline_volume = statistics.median(int(row["trade_volume"]) for row in volume_rows)
        if baseline_volume <= 0:
            return {
                **base,
                "data_quality": "BASELINE_VOLUME_ZERO",
                "why_selected": "此前20日成交量中位数为0，无法计算Relative Volume。",
            }
        recent_rows = prior[-self.config.quiet_recent_sessions :]
        recent_volume = statistics.median(int(row["trade_volume"]) for row in recent_rows)
        volume_ratio = current_volume / baseline_volume
        recent_to_normal = recent_volume / baseline_volume
        current_to_recent = current_volume / recent_volume if recent_volume > 0 else None
        change_pct = (current_close / previous_close - 1) * 100

        prior_20d_high = max(float(row["highest_price"]) for row in prior[-20:])
        prior_40d_high = max(float(row["highest_price"]) for row in prior[-40:]) if len(prior) >= 40 else None
        breakout_20d = current_close > prior_20d_high
        breakout_40d = prior_40d_high is not None and current_close > prior_40d_high
        intraday_breakout_20d = float(current["highest_price"]) > prior_20d_high
        intraday_breakout_40d = prior_40d_high is not None and float(current["highest_price"]) > prior_40d_high
        breakout_20d_pct = (current_close / prior_20d_high - 1) * 100
        breakout_40d_pct = (current_close / prior_40d_high - 1) * 100 if prior_40d_high else None
        breakout_pct = max(value for value in (breakout_20d_pct, breakout_40d_pct) if value is not None)

        return_window = prior_returns[-self.config.price_return_sessions :]
        historical_volatility = statistics.stdev(return_window) if len(return_window) >= 2 else None
        historical_mean = statistics.mean(return_window) if return_window else None
        price_zscore = (
            (change_pct - historical_mean) / historical_volatility
            if historical_volatility not in (None, 0) and historical_mean is not None
            else None
        )
        price_percentile = (
            100 * sum(abs(value) <= abs(change_pct) for value in return_window) / len(return_window)
            if return_window
            else None
        )

        matched: list[str] = []
        severity: dict[str, Any] = {}
        if volume_ratio >= self.config.volume_spike_ratio:
            matched.append("VOLUME_SPIKE")
            severity["VOLUME_SPIKE"] = {"volume_ratio": volume_ratio, "threshold_multiple": volume_ratio / self.config.volume_spike_ratio}
        if breakout_20d:
            matched.append("RANGE_BREAKOUT_20D")
            severity["RANGE_BREAKOUT_20D"] = {"breakout_pct": breakout_20d_pct}
        if breakout_40d:
            matched.append("RANGE_BREAKOUT_40D")
            severity["RANGE_BREAKOUT_40D"] = {"breakout_pct": breakout_40d_pct}
        if (breakout_20d or breakout_40d) and volume_ratio >= self.config.volume_spike_ratio:
            matched.append("PRICE_VOLUME_BREAKOUT")
            severity["PRICE_VOLUME_BREAKOUT"] = {"volume_ratio": volume_ratio, "breakout_pct": breakout_pct}
        quiet_hit = (
            recent_to_normal <= self.config.quiet_recent_to_normal_max
            and volume_ratio >= self.config.quiet_current_to_normal_min
            and current_to_recent is not None
            and current_to_recent >= self.config.quiet_current_to_recent_min
        )
        if quiet_hit:
            matched.append("QUIET_TO_VOLUME_SPIKE")
            severity["QUIET_TO_VOLUME_SPIKE"] = {
                "recent5_to_20d_ratio": recent_to_normal,
                "current_to_recent5_ratio": current_to_recent,
            }
        if price_zscore is not None and abs(price_zscore) >= self.config.price_anomaly_abs_zscore:
            matched.append("PRICE_ANOMALY")
            severity["PRICE_ANOMALY"] = {
                "price_zscore": price_zscore,
                "threshold_multiple": abs(price_zscore) / self.config.price_anomaly_abs_zscore,
            }

        data_quality = "COMPLETE"
        if len(prior) < 40:
            data_quality = "PARTIAL_40D_RANGE"
        if price_zscore is None:
            data_quality = "PARTIAL_PRICE_HISTORY"
        metrics = {
            "close": current_close,
            "change_pct": change_pct,
            "current_volume": current_volume,
            "median_volume_20d": baseline_volume,
            "volume_ratio": volume_ratio,
            "median_volume_recent5d": recent_volume,
            "recent5_to_20d_volume_ratio": recent_to_normal,
            "current_to_recent5_volume_ratio": current_to_recent,
            "prior_20d_high": prior_20d_high,
            "prior_40d_high": prior_40d_high,
            "breakout_20d": breakout_20d,
            "breakout_40d": breakout_40d,
            "intraday_breakout_20d": intraday_breakout_20d,
            "intraday_breakout_40d": intraday_breakout_40d,
            "breakout_pct": breakout_pct,
            "historical_volatility": historical_volatility,
            "price_zscore": price_zscore,
            "abs_price_zscore": abs(price_zscore) if price_zscore is not None else None,
            "price_percentile": price_percentile,
            "prior_sessions": len(prior),
        }
        why = self._why_selected(matched, metrics)
        return {
            **base,
            "matched_rules": matched,
            "rule_severity": severity,
            "raw_metrics": metrics,
            "why_selected": why,
            "data_quality": data_quality,
        }

    @staticmethod
    def _assign_liquidity_context(results: list[dict[str, Any]]) -> None:
        """Attach cross-sectional liquidity context without changing anomaly ranking."""
        by_market = {
            market: sorted(
                int(row["raw_metrics"]["current_volume"])
                for row in results
                if row["market"] == market
            )
            for market in ("TWSE", "TPEX")
        }
        for row in results:
            volumes = by_market[row["market"]]
            volume = int(row["raw_metrics"]["current_volume"])
            lower = bisect_left(volumes, volume)
            upper = bisect_right(volumes, volume)
            percentile = 100.0 * ((lower + upper) / 2) / len(volumes)
            if percentile <= LIQUIDITY_LOW_MAX_PERCENTILE:
                level = "LOW"
            elif percentile >= LIQUIDITY_HIGH_MIN_PERCENTILE:
                level = "HIGH"
            else:
                level = "MEDIUM"
            row["median_volume_20d"] = row["raw_metrics"].get("median_volume_20d")
            row["market_volume_percentile"] = percentile
            row["liquidity_level"] = level
            row["raw_metrics"]["market_volume_percentile"] = percentile
            row["raw_metrics"]["liquidity_level"] = level

    @staticmethod
    def _why_selected(matched: list[str], metrics: dict[str, Any]) -> str:
        if not matched:
            return "当日未达到V0.1任何异常门槛，保留计算结果但不进入Top 20。"
        parts: list[str] = []
        if "QUIET_TO_VOLUME_SPIKE" in matched:
            parts.append(
                f"此前5日中位量仅为20日中位量{metrics['recent5_to_20d_volume_ratio']:.2f}倍，"
                f"今日放大至近期5日中位量{metrics['current_to_recent5_volume_ratio']:.2f}倍"
            )
        elif "VOLUME_SPIKE" in matched:
            parts.append(f"今日成交量达到此前20日中位数{metrics['volume_ratio']:.2f}倍")
        if "PRICE_VOLUME_BREAKOUT" in matched:
            windows = []
            if metrics["breakout_20d"]:
                windows.append("20日")
            if metrics["breakout_40d"]:
                windows.append("40日")
            parts.append(f"收盘确认突破此前{'及'.join(windows)}区间高点{metrics['breakout_pct']:.2f}%，形成量价共振")
        elif "RANGE_BREAKOUT_20D" in matched or "RANGE_BREAKOUT_40D" in matched:
            parts.append(f"收盘确认区间突破{metrics['breakout_pct']:.2f}%，但成交量未达到2倍门槛")
        elif "VOLUME_SPIKE" in matched:
            parts.append("收盘未确认突破历史区间，因此属于放量而非量价突破")
        if "PRICE_ANOMALY" in matched:
            parts.append(
                f"当日涨跌{metrics['change_pct']:+.2f}%，偏离自身近期正常波动{abs(metrics['price_zscore']):.2f}个标准差"
            )
        return "；".join(parts) + "。"

    @staticmethod
    def _ranking_key(row: dict[str, Any]) -> tuple[Any, ...]:
        metrics = row["raw_metrics"]
        return (
            -len(row["matched_rules"]),
            -int("PRICE_VOLUME_BREAKOUT" in row["matched_rules"]),
            -float(metrics.get("volume_ratio") or 0),
            -float(metrics.get("abs_price_zscore") or 0),
            -float(metrics.get("breakout_pct") or -999),
            row["security_id"],
        )

    @staticmethod
    def _audit_cases(results: list[dict[str, Any]], excluded: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = [row for row in results if row["matched_rules"]]
        case_a = max(
            (row for row in results if "VOLUME_SPIKE" not in row["matched_rules"]),
            key=lambda row: row["raw_metrics"].get("current_volume") or 0,
            default=None,
        )
        case_b = max(
            (row for row in ranked if (row["raw_metrics"].get("volume_ratio") or 0) >= 5),
            key=lambda row: row["raw_metrics"].get("volume_ratio") or 0,
            default=None,
        )
        case_c = max(
            (
                row for row in results
                if (row["raw_metrics"].get("change_pct") or 0) > 0
                and "PRICE_ANOMALY" in row["matched_rules"]
                and "VOLUME_SPIKE" not in row["matched_rules"]
            ),
            key=lambda row: row["raw_metrics"].get("change_pct") or 0,
            default=None,
        )
        case_d = max(
            (
                row for row in ranked
                if "VOLUME_SPIKE" in row["matched_rules"]
                and "RANGE_BREAKOUT_20D" not in row["matched_rules"]
                and "RANGE_BREAKOUT_40D" not in row["matched_rules"]
            ),
            key=lambda row: row["raw_metrics"].get("volume_ratio") or 0,
            default=None,
        )
        case_e = next((row for row in excluded if row["data_quality"] == "INSUFFICIENT_HISTORY"), None)

        def compact(row: dict[str, Any] | None) -> dict[str, Any] | None:
            if row is None:
                return None
            return {
                "security_id": row["security_id"],
                "name": row["name"],
                "data_quality": row["data_quality"],
                "matched_rules": row["matched_rules"],
                "raw_metrics": row["raw_metrics"],
                "why_selected": row["why_selected"],
            }

        return {
            "A_large_absolute_volume_not_relative_anomaly": compact(case_a),
            "B_low_normal_volume_sudden_spike": compact(case_b),
            "C_price_move_without_volume": compact(case_c),
            "D_volume_without_breakout": compact(case_d),
            "E_insufficient_history_excluded": compact(case_e),
        }
