import requests
import pandas as pd
import logging
from typing import List
import yfinance as yf

logger = logging.getLogger(__name__)

# Fallback top liquid Nifty 500 stocks list (NSE tickers)
FALLBACK_NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LTIM.NS",
    "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "HCLTECH.NS", "ASIANPAINT.NS",
    "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS",
    "TATAMOTORS.NS", "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "M&M.NS",
    "JSWSTEEL.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "ONGC.NS",
    "BAJAJFINSV.NS", "GRASIM.NS", "TECHM.NS", "HDFCLIFE.NS", "BRITANNIA.NS",
    "WIPRO.NS", "HINDALCO.NS", "DRREDDY.NS", "EICHERMOT.NS", "CIPLA.NS",
    "SBILIFE.NS", "APOLLOHOSP.NS", "DIVISLAB.NS", "TATACONSUM.NS", "BPCL.NS",
    "HEROMOTOCO.NS", "INDUSINDBK.NS", "NESTLEIND.NS", "BEL.NS", "HAL.NS",
    "TRENT.NS", "ZOMATO.NS", "VBL.NS", "DLF.NS", "IOC.NS", "GAIL.NS",
    "PIDILITIND.NS", "SIEMENS.NS", "ABB.NS", "BANKBARODA.NS", "PFC.NS",
    "REC.NS", "CHOLAFIN.NS", "TATAELXSI.NS", "POLYCAB.NS", "JIOFIN.NS"
]


def fetch_nifty_500_tickers_online() -> List[str]:
    """
    Fetches official Nifty 500 stock symbols from NSE website / GitHub CSV.
    """
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        df = pd.read_csv(url)
        if "Symbol" in df.columns:
            symbols = [f"{sym.strip()}.NS" for sym in df["Symbol"].dropna().tolist()]
            logger.info(f"Successfully fetched {len(symbols)} Nifty 500 symbols from NSE.")
            return symbols
    except Exception as e:
        logger.warning(f"Failed to fetch Nifty 500 online list: {e}. Using fallback list.")

    return FALLBACK_NIFTY_SYMBOLS


def get_nifty_500_symbols(use_online_fetch: bool = True) -> List[str]:
    """
    Returns list of Nifty 500 stock symbols.
    """
    if use_online_fetch:
        symbols = fetch_nifty_500_tickers_online()
        if symbols:
            return symbols
    return FALLBACK_NIFTY_SYMBOLS


def fetch_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetches OHLCV historical data for a given ticker symbol using yfinance.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            logger.warning(f"No data returned for symbol {symbol}")
            return None
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None
