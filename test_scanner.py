import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from nifty_symbols import get_nifty_500_symbols, get_crypto_symbols
from liquidity_engine import LiquidityDetector
from scanner import NiftyLiquidityScanner
from notifier import format_ascii_table, export_scan_results


def create_sample_ohlcv(length=60, seed=42) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=length, freq="D")
    np.random.seed(seed)
    base_price = 100 + np.random.randn(length).cumsum()
    
    df = pd.DataFrame({
        "Open": base_price,
        "High": base_price + np.abs(np.random.randn(length)) + 1.0,
        "Low": base_price - np.abs(np.random.randn(length)) - 1.0,
        "Close": base_price + np.random.randn(length) * 0.5,
        "Volume": np.random.randint(100000, 300000, length)
    }, index=dates)

    df["Turnover"] = df["Close"] * df["Volume"]
    return df


def test_nifty_symbols_fallback():
    symbols = get_nifty_500_symbols(use_online_fetch=False)
    assert isinstance(symbols, list)
    assert len(symbols) >= 50
    assert "RELIANCE.NS" in symbols
    assert "TCS.NS" in symbols


def test_get_crypto_symbols():
    symbols = get_crypto_symbols()
    assert isinstance(symbols, list)
    assert len(symbols) >= 10
    assert "BTC-USD" in symbols
    assert "ETH-USD" in symbols
    assert "SOL-USD" in symbols


def test_crypto_format_ascii_table():
    sample_results = [
        {
            "symbol": "BTC-USD",
            "close": 65432.10,
            "vol_spike_ratio": 4.5,
            "turnover_cr": 500.0,
            "liquidity_score": 90.0,
            "signals": ["BULLISH_LIQUIDITY_SWEEP", "MAJOR_VOLUME_SPIKE"]
        }
    ]
    table = format_ascii_table(sample_results)
    assert "BTC-USD" in table
    assert "65432.1" in table
    assert "$5.00B" in table
    assert "90" in table


def test_liquidity_detector_volume_spike():
    df = create_sample_ohlcv(length=50)
    # Inject a massive volume spike on the last row
    df.loc[df.index[-1], "Volume"] = int(df["Volume"].mean() * 5.0)
    df.loc[df.index[-1], "Turnover"] = df.loc[df.index[-1], "Close"] * df.loc[df.index[-1], "Volume"]

    detector = LiquidityDetector(volume_spike_threshold=2.0)
    res = detector.analyze_stock(df, "TEST.NS")

    assert res["valid"] is True
    assert res["vol_spike_ratio"] > 3.0
    assert "MAJOR_VOLUME_SPIKE" in res["signals"]
    assert res["liquidity_score"] >= 40.0


def test_liquidity_detector_bullish_sweep():
    df = create_sample_ohlcv(length=60)
    detector = LiquidityDetector(wick_ratio_threshold=0.3)
    
    # Force a swing low around index 30
    df.loc[df.index[30], "Low"] = 80.0
    df.loc[df.index[25:36], "Low"] = np.maximum(df.loc[df.index[25:36], "Low"], 85.0)
    df.loc[df.index[30], "Low"] = 80.0

    # Last candle dips below 80.0 but closes above
    df.loc[df.index[-1], "Low"] = 78.0
    df.loc[df.index[-1], "Close"] = 82.0
    df.loc[df.index[-1], "Open"] = 83.0
    df.loc[df.index[-1], "High"] = 84.0
    df.loc[df.index[-1], "Volume"] = 500000

    res = detector.analyze_stock(df, "BULLISH.NS")

    assert res["valid"] is True
    assert res["bullish_sweep"] is True
    assert "BULLISH_LIQUIDITY_SWEEP" in res["signals"]


def test_liquidity_detector_bearish_sweep():
    df = create_sample_ohlcv(length=60)
    detector = LiquidityDetector(wick_ratio_threshold=0.3)

    # Force a swing high around index 30
    df.loc[df.index[30], "High"] = 120.0
    df.loc[df.index[25:36], "High"] = np.minimum(df.loc[df.index[25:36], "High"], 115.0)
    df.loc[df.index[30], "High"] = 120.0

    # Last candle pierces above 120.0 but closes back below with upper wick
    df.loc[df.index[-1], "High"] = 122.0
    df.loc[df.index[-1], "Close"] = 118.0
    df.loc[df.index[-1], "Open"] = 117.0
    df.loc[df.index[-1], "Low"] = 115.0
    df.loc[df.index[-1], "Volume"] = 500000

    res = detector.analyze_stock(df, "BEARISH.NS")

    assert res["valid"] is True
    assert res["bearish_sweep"] is True
    assert "BEARISH_LIQUIDITY_SWEEP" in res["signals"]


def test_format_ascii_table():
    sample_results = [
        {
            "symbol": "RELIANCE.NS",
            "close": 2900.50,
            "vol_spike_ratio": 3.2,
            "turnover_cr": 450.0,
            "liquidity_score": 85.0,
            "signals": ["BULLISH_LIQUIDITY_SWEEP", "MAJOR_VOLUME_SPIKE"]
        }
    ]
    table = format_ascii_table(sample_results)
    assert "RELIANCE" in table
    assert "2900.5" in table
    assert "85" in table


def test_export_scan_results():
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_results = [
            {
                "symbol": "TCS.NS",
                "close": 4000.0,
                "vol_spike_ratio": 2.5,
                "turnover_cr": 300.0,
                "liquidity_score": 75.0,
                "signals": ["MAJOR_VOLUME_SPIKE"]
            }
        ]
        exported = export_scan_results(sample_results, output_dir=tmpdir, prefix="test_report")
        assert os.path.exists(exported["csv"])
        assert os.path.exists(exported["json"])
