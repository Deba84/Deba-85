import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple

class LiquidityDetector:
    def __init__(
        self,
        pivot_window: int = 5,
        volume_sma_period: int = 20,
        volume_spike_threshold: float = 2.0,
        wick_ratio_threshold: float = 0.35,
        eq_tolerance_pct: float = 0.35
    ):
        self.pivot_window = pivot_window
        self.volume_sma_period = volume_sma_period
        self.volume_spike_threshold = volume_spike_threshold
        self.wick_ratio_threshold = wick_ratio_threshold
        self.eq_tolerance_pct = eq_tolerance_pct

    def analyze_stock(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Runs comprehensive liquidity detection algorithms on OHLCV DataFrame.
        """
        if df is None or len(df) < self.volume_sma_period + self.pivot_window * 2:
            return {"symbol": symbol, "valid": False, "reason": "Insufficient data"}

        data = df.copy()

        # Calculate volume moving average & volume spike ratio
        data["Vol_SMA"] = data["Volume"].rolling(window=self.volume_sma_period).mean()
        data["Vol_Spike_Ratio"] = data["Volume"] / data["Vol_SMA"].replace(0, np.nan)
        
        # Calculate Turnover (Close * Volume) in Crore INR (1 Crore = 10,000,000)
        data["Turnover"] = data["Close"] * data["Volume"]
        data["Turnover_Cr"] = data["Turnover"] / 1e7
        data["Turnover_SMA_Cr"] = data["Turnover"].rolling(window=self.volume_sma_period).mean() / 1e7

        # Candle metrics
        candle_range = (data["High"] - data["Low"]).replace(0, np.nan)
        data["Upper_Wick"] = data["High"] - data[["Open", "Close"]].max(axis=1)
        data["Lower_Wick"] = data[["Open", "Close"]].min(axis=1) - data["Low"]
        data["Upper_Wick_Ratio"] = data["Upper_Wick"] / candle_range
        data["Lower_Wick_Ratio"] = data["Lower_Wick"] / candle_range

        # Identify Swing Highs and Swing Lows
        data["Swing_High"] = False
        data["Swing_Low"] = False

        w = self.pivot_window
        for i in range(w, len(data) - w):
            high_window = data["High"].iloc[i - w : i + w + 1]
            low_window = data["Low"].iloc[i - w : i + w + 1]
            if data["High"].iloc[i] == high_window.max():
                data.iloc[i, data.columns.get_loc("Swing_High")] = True
            if data["Low"].iloc[i] == low_window.min():
                data.iloc[i, data.columns.get_loc("Swing_Low")] = True

        latest_idx = len(data) - 1
        latest = data.iloc[latest_idx]

        # Get recent swing highs/lows prior to latest candle
        prior_data = data.iloc[max(0, latest_idx - 60) : latest_idx]
        swing_highs = prior_data[prior_data["Swing_High"]]["High"].values
        swing_lows = prior_data[prior_data["Swing_Low"]]["Low"].values

        # Detect Liquidity Sweeps
        bullish_sweep = False
        bearish_sweep = False
        near_sweep_bullish = False
        near_sweep_bearish = False
        swept_level = None

        if len(swing_lows) > 0:
            recent_low = np.min(swing_lows[-3:]) if len(swing_lows) >= 3 else np.min(swing_lows)
            # Dips below recent low but closes back above
            if latest["Low"] < recent_low and latest["Close"] > recent_low and latest["Lower_Wick_Ratio"] >= self.wick_ratio_threshold:
                bullish_sweep = True
                swept_level = float(recent_low)
            # Near sweep setup: Price within 1.5% above key swing low
            elif 0 < (latest["Low"] - recent_low) / max(recent_low, 1e-5) <= 0.015:
                near_sweep_bullish = True
                swept_level = float(recent_low)

        if len(swing_highs) > 0:
            recent_high = np.max(swing_highs[-3:]) if len(swing_highs) >= 3 else np.max(swing_highs)
            # Pierces above recent high but closes back below
            if latest["High"] > recent_high and latest["Close"] < recent_high and latest["Upper_Wick_Ratio"] >= self.wick_ratio_threshold:
                bearish_sweep = True
                swept_level = float(recent_high)
            # Near sweep setup: Price within 1.5% below key swing high
            elif 0 < (recent_high - latest["High"]) / max(recent_high, 1e-5) <= 0.015:
                near_sweep_bearish = True
                swept_level = float(recent_high)

        # Detect Equal Highs (EQH) or Equal Lows (EQL) Liquidity Pools
        eqh_detected, eql_detected = self._detect_equal_levels(data)

        # Volume spike analysis
        vol_ratio = float(latest["Vol_Spike_Ratio"]) if not np.isnan(latest["Vol_Spike_Ratio"]) else 1.0
        is_volume_spike = vol_ratio >= self.volume_spike_threshold

        # Breakout Liquidity
        lookback_max = prior_data["High"].max() if not prior_data.empty else latest["High"]
        is_breakout = (latest["Close"] > lookback_max) and vol_ratio >= 1.8

        # Determine Signal Category
        signals = []
        if bullish_sweep:
            signals.append("BULLISH_LIQUIDITY_SWEEP")
        elif near_sweep_bullish:
            signals.append("NEAR_BULLISH_SWEEP_ZONE")

        if bearish_sweep:
            signals.append("BEARISH_LIQUIDITY_SWEEP")
        elif near_sweep_bearish:
            signals.append("NEAR_BEARISH_SWEEP_ZONE")

        if is_volume_spike:
            signals.append("MAJOR_VOLUME_SPIKE")
        if is_breakout:
            signals.append("HIGH_LIQUIDITY_BREAKOUT")
        if eqh_detected:
            signals.append("EQH_LIQUIDITY_POOL")
        if eql_detected:
            signals.append("EQL_LIQUIDITY_POOL")

        primary_signal = signals[0] if signals else "NEUTRAL"

        # Calculate Liquidity Score (0 to 100)
        score = self._calculate_liquidity_score(
            vol_ratio=vol_ratio,
            bullish_sweep=bullish_sweep,
            bearish_sweep=bearish_sweep,
            is_breakout=is_breakout,
            eqh=eqh_detected,
            eql=eql_detected,
            turnover_cr=float(latest["Turnover_Cr"])
        )

        return {
            "symbol": symbol,
            "valid": True,
            "date": str(latest.name.date()) if hasattr(latest.name, "date") else str(latest.name),
            "close": float(latest["Close"]),
            "volume": int(latest["Volume"]),
            "vol_sma": float(latest["Vol_SMA"]) if not np.isnan(latest["Vol_SMA"]) else 0.0,
            "vol_spike_ratio": round(vol_ratio, 2),
            "turnover_cr": round(float(latest["Turnover_Cr"]), 2),
            "primary_signal": primary_signal,
            "signals": signals,
            "liquidity_score": score,
            "bullish_sweep": bullish_sweep,
            "bearish_sweep": bearish_sweep,
            "near_sweep_bullish": near_sweep_bullish,
            "near_sweep_bearish": near_sweep_bearish,
            "swept_level": swept_level,
            "is_breakout": is_breakout,
            "eqh_liquidity_pool": eqh_detected,
            "eql_liquidity_pool": eql_detected
        }

    def _detect_equal_levels(self, df: pd.DataFrame) -> Tuple[bool, bool]:
        """
        Detects Equal Highs (EQH) or Equal Lows (EQL) within the last 30 periods.
        """
        recent = df.tail(30)
        highs = recent["High"].values
        lows = recent["Low"].values

        eqh = False
        eql = False

        # Compare pairs of local peaks/troughs
        for i in range(len(highs)):
            for j in range(i + 3, len(highs)):
                diff_high = abs(highs[i] - highs[j]) / max(highs[i], 1e-5) * 100
                if diff_high <= self.eq_tolerance_pct:
                    eqh = True
                    break

        for i in range(len(lows)):
            for j in range(i + 3, len(lows)):
                diff_low = abs(lows[i] - lows[j]) / max(lows[i], 1e-5) * 100
                if diff_low <= self.eq_tolerance_pct:
                    eql = True
                    break

        return eqh, eql

    def _calculate_liquidity_score(
        self,
        vol_ratio: float,
        bullish_sweep: bool,
        bearish_sweep: bool,
        is_breakout: bool,
        eqh: bool,
        eql: bool,
        turnover_cr: float
    ) -> float:
        """
        Calculates composite Liquidity Score (0-100).
        """
        score = 0.0

        # Volume Multiple Weight (max 40 pts)
        vol_pts = min(40.0, (vol_ratio / 3.0) * 40.0)
        score += vol_pts

        # Signal Weights (max 35 pts)
        if bullish_sweep or bearish_sweep:
            score += 25.0
        if is_breakout:
            score += 15.0

        # Liquidity Pool Presence (max 15 pts)
        if eqh or eql:
            score += 10.0

        # Turnover liquidity adjustment (max 10 pts)
        if turnover_cr >= 50.0:
            score += 10.0
        elif turnover_cr >= 10.0:
            score += 5.0

        return min(100.0, round(score, 1))
