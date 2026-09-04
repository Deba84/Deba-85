import logging
from typing import Dict, Any, Optional
import yfinance as yf

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    def __init__(
        self,
        min_market_cap_cr: float = 500.0,
        max_pe: float = 75.0,
        min_roe_pct: float = 8.0,
        max_debt_to_equity: float = 2.5
    ):
        self.min_market_cap_cr = min_market_cap_cr
        self.max_pe = max_pe
        self.min_roe_pct = min_roe_pct
        self.max_debt_to_equity = max_debt_to_equity

    def analyze_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches fundamental metrics for a symbol and returns health status.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
        except Exception as e:
            logger.warning(f"Failed to fetch fundamental data for {symbol}: {e}")
            info = {}

        # Raw values
        market_cap_raw = info.get("marketCap")
        pe_ratio_raw = info.get("trailingPE") or info.get("forwardPE")
        roe_raw = info.get("returnOnEquity")  # ratio e.g. 0.15 = 15%
        debt_to_equity_raw = info.get("debtToEquity")  # ratio or percentage
        earnings_growth_raw = info.get("earningsGrowth")
        profit_margins_raw = info.get("profitMargins")

        # Convert Market Cap to Crores (INR) or Millions (USD)
        # 1 Cr INR = 10,000,000
        market_cap_cr = (market_cap_raw / 1e7) if market_cap_raw else None

        # Clean ratios
        pe_ratio = float(pe_ratio_raw) if pe_ratio_raw is not None else None
        roe_pct = (float(roe_raw) * 100.0) if roe_raw is not None else None

        # Debt to equity: yfinance sometimes returns percentage (e.g. 50 = 0.5)
        debt_to_equity = None
        if debt_to_equity_raw is not None:
            val = float(debt_to_equity_raw)
            debt_to_equity = val / 100.0 if val > 10 else val

        earnings_growth_pct = (float(earnings_growth_raw) * 100.0) if earnings_growth_raw is not None else None
        profit_margins_pct = (float(profit_margins_raw) * 100.0) if profit_margins_raw is not None else None

        # Fundamental criteria checks
        checks = {}
        score = 0.0
        max_possible = 100.0

        # 1. Market Cap Check (25 pts)
        if market_cap_cr is not None:
            if market_cap_cr >= self.min_market_cap_cr:
                checks["market_cap_pass"] = True
                score += 25.0
            else:
                checks["market_cap_pass"] = False
        else:
            # Neutral / missing assumption for fallback
            checks["market_cap_pass"] = True
            score += 15.0

        # 2. Valuation P/E Check (25 pts)
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio <= self.max_pe:
                checks["pe_pass"] = True
                score += 25.0
            else:
                checks["pe_pass"] = False
        else:
            checks["pe_pass"] = True
            score += 15.0

        # 3. Profitability / ROE Check (25 pts)
        if roe_pct is not None:
            if roe_pct >= self.min_roe_pct:
                checks["roe_pass"] = True
                score += 25.0
            else:
                checks["roe_pass"] = False
        else:
            checks["roe_pass"] = True
            score += 15.0

        # 4. Solvency / Debt Check (25 pts)
        if debt_to_equity is not None:
            if debt_to_equity <= self.max_debt_to_equity:
                checks["debt_pass"] = True
                score += 25.0
            else:
                checks["debt_pass"] = False
        else:
            checks["debt_pass"] = True
            score += 15.0

        is_strong = score >= 60.0 and checks.get("market_cap_pass", True) and checks.get("pe_pass", True)

        return {
            "symbol": symbol,
            "market_cap_cr": round(market_cap_cr, 2) if market_cap_cr else None,
            "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
            "roe_pct": round(roe_pct, 2) if roe_pct else None,
            "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity else None,
            "earnings_growth_pct": round(earnings_growth_pct, 2) if earnings_growth_pct else None,
            "profit_margins_pct": round(profit_margins_pct, 2) if profit_margins_pct else None,
            "fundamental_score": round(score, 1),
            "is_fundamental_strong": is_strong,
            "checks": checks
        }
