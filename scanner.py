import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from nifty_symbols import get_nifty_500_symbols, get_crypto_symbols, fetch_stock_data
from liquidity_engine import LiquidityDetector

logger = logging.getLogger(__name__)


class NiftyLiquidityScanner:
    def __init__(self, config_path: Optional[str] = "config.json"):
        self.config = self._load_config(config_path)
        scan_cfg = self.config.get("scan_settings", {})

        self.pivot_window = scan_cfg.get("pivot_window", 5)
        self.volume_sma_period = scan_cfg.get("volume_sma_period", 20)
        self.volume_spike_threshold = scan_cfg.get("volume_spike_threshold", 2.0)
        self.wick_ratio_threshold = scan_cfg.get("liquidity_grab_wick_ratio", 0.35)
        self.min_turnover_cr = scan_cfg.get("min_turnover_cr", 1.0)

        self.detector = LiquidityDetector(
            pivot_window=self.pivot_window,
            volume_sma_period=self.volume_sma_period,
            volume_spike_threshold=self.volume_spike_threshold,
            wick_ratio_threshold=self.wick_ratio_threshold
        )

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config file {config_path}: {e}")
        return {}

    def scan_symbol(self, symbol: str, period: str = "1y", interval: str = "1d") -> Optional[Dict[str, Any]]:
        """
        Fetches data and scans a single symbol.
        """
        df = fetch_stock_data(symbol, period=period, interval=interval)
        if df is None or df.empty:
            return None

        res = self.detector.analyze_stock(df, symbol)
        if res.get("valid"):
            return res
        return None

    def scan_market(
        self,
        symbols: Optional[List[str]] = None,
        market: str = "nifty",
        period: str = "1y",
        interval: str = "1d",
        max_workers: int = 10,
        min_score: float = 0.0,
        signal_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scans a list of tickers (Nifty stocks, Crypto pairs, or custom) using multi-threading.
        """
        if not symbols:
            if market.lower() in ["crypto", "cryptocurrency"]:
                symbols = get_crypto_symbols()
            elif market.lower() in ["all", "both"]:
                symbols = get_nifty_500_symbols(use_online_fetch=True) + get_crypto_symbols()
            else:
                symbols = get_nifty_500_symbols(use_online_fetch=True)

        logger.info(f"Starting Nifty Liquidity scan on {len(symbols)} symbols...")
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.scan_symbol, sym, period, interval): sym
                for sym in symbols
            }

            for future in as_completed(future_to_symbol):
                sym = future_to_symbol[future]
                try:
                    res = future.result()
                    if res:
                        # Apply turnover filter
                        if res.get("turnover_cr", 0.0) < self.min_turnover_cr:
                            continue
                        
                        # Apply score filter
                        if res.get("liquidity_score", 0.0) < min_score:
                            continue

                        # Apply signal filter
                        if signal_filter:
                            filter_upper = signal_filter.upper()
                            signals = [s.upper() for s in res.get("signals", [])]
                            if filter_upper not in signals and filter_upper not in res.get("primary_signal", "").upper():
                                continue

                        results.append(res)
                except Exception as e:
                    logger.error(f"Error scanning symbol {sym}: {e}")

        # Sort results by liquidity score descending
        results.sort(key=lambda x: x.get("liquidity_score", 0.0), reverse=True)
        return results
