import os
import json
import logging
import requests
import pandas as pd
import yfinance as yf
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Primary fallback list of Nifty 500 stock tickers (with .NS extension for Yahoo Finance)
NIFTY_500_FALLBACK = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LTIM.NS", "LT.NS",
    "HINDUNILVR.NS", "AXISBANK.NS", "KOTAKBANK.NS", "TATAMOTORS.NS", "M&M.NS",
    "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "NTPC.NS", "POWERGRID.NS", "ULTRACEMCO.NS", "TATASTEEL.NS", "COALINDIA.NS",
    "BAJFINANCE.NS", "BAJAJFINSV.NS", "ASIANPAINT.NS", "ONGC.NS", "JSWSTEEL.NS",
    "VEDL.NS", "HAL.NS", "BEL.NS", "SIEMENS.NS", "DLF.NS",
    "IOC.NS", "BPCL.NS", "GAIL.NS", "ZOMATO.NS", "JIOFIN.NS",
    "TRENT.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "MAXHEALTH.NS", "DMART.NS",
    "APOLLOHOSP.NS", "DIVISLAB.NS", "DRREDDY.NS", "CIPLA.NS", "EICHERMOT.NS",
    "TVSMOTOR.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "PIDILITIND.NS", "GRASIM.NS",
    "BRITANNIA.NS", "NESTLEIND.NS", "INDIGO.NS", "TATACOMM.NS", "TATACONSUM.NS",
    "HDFCLIFE.NS", "SBILIFE.NS", "ICICIPRULI.NS", "ICICIGI.NS", "AMBUJACEM.NS",
    "ACC.NS", "SHREECEM.NS", "DALBHARAT.NS", "HAVELLS.NS", "POLYCAB.NS",
    "KEI.NS", "DIXON.NS", "KALYANKJIL.NS", "PERSISTENT.NS", "COFORGE.NS",
    "MPHASIS.NS", "TATAELXSI.NS", "TECHM.NS", "WIPRO.NS", "HCLTECH.NS",
    "OFSS.NS", "CYIENT.NS", "KPITTECH.NS", "LTTS.NS", "TATAINVEST.NS",
    "BOSCHLTD.NS", "MOTHERSON.NS", "BALKRISIND.NS", "MRF.NS", "APOLLOTYRE.NS",
    "BHARATFORG.NS", "ASHOKLEY.NS", "EICHERMOT.NS", "ESCORTS.NS", "TIINDIA.NS",
    "TATASTEEL.NS", "JINDALSTEL.NS", "NMDC.NS", "NATIONALUM.NS", "HINDALCO.NS",
    "SAIL.NS", "HINDZINC.NS", "APLAPOLLO.NS", "RATNAMANI.NS", "GODREJPROP.NS",
    "OBEROIRAL.NS", "PHOENIXLTD.NS", "PRESTIGE.NS", "BRIGADE.NS", "LODHA.NS",
    "MACPOWER.NS", "INDHOTEL.NS", "EIHOTEL.NS", "DEVYANI.NS", "JUBLFOOD.NS",
    "WESTLIFE.NS", "SAPPHIRE.NS", "VARUN.NS", "VBL.NS", "UBL.NS",
    "MCDOWELL-N.NS", "RADICO.NS", "TATACHEM.NS", "UPL.NS", "PIIND.NS",
    "SRF.NS", "AARTIIND.NS", "DEEPAKNTR.NS", "GUJGASLTD.NS", "IGL.NS",
    "MGL.NS", "ATGL.NS", "PETRONET.NS", "OIL.NS", "HINDPETRO.NS",
    "BHEL.NS", "CGPOWER.NS", "ABB.NS", "SUZLON.NS", "INOXWIND.NS",
    "TORNTPOWER.NS", "CESC.NS", "NHPC.NS", "SJVN.NS", "NLCINDIA.NS",
    "IREDA.NS", "REC.NS", "PFC.NS", "HUDCO.NS", "IRFC.NS",
    "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "TITAGARH.NS", "JWL.NS",
    "MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS", "BDL.NS", "SOLARINDS.NS",
    "CANBK.NS", "PNB.NS", "BANKBARODA.NS", "UNIONBANK.NS", "INDIANB.NS",
    "IOB.NS", "UCOBANK.NS", "CENTRALBK.NS", "BANKINDIA.NS", "MAHABANK.NS",
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANDHANBNK.NS", "AUBANK.NS", "INDUSINDBK.NS",
    "YESBANK.NS", "RBLBANK.NS", "KARURVYSYA.NS", "CITYUNIONB.NS", "CUB.NS",
    "MUTHOOTFIN.NS", "MANAPPURAM.NS", "POONAWALLA.NS", "L&TFH.NS", "M&MFIN.NS",
    "LICHSGFIN.NS", "HOMEFIRST.NS", "AAVAS.NS", "CANFINHOME.NS", "PNBHOUSING.NS",
    "LICI.NS", "GICRE.NS", "NIACL.NS", "STARHEALTH.NS", "MEDANTA.NS",
    "FORTIS.NS", "MAXHEALTH.NS", "KIMS.NS", "RAINBOW.NS", "ASTERDM.NS",
    "SYNGENE.NS", "BIOCON.NS", "LUPIN.NS", "GLENMARK.NS", "TORNTPHARM.NS",
    "ZYDUSLIFE.NS", "MANKIND.NS", "IPCALAB.NS", "AJANTPHARM.NS", "ALKEM.NS",
    "LAURUSLABS.NS", "GRANULES.NS", "NATCOPHARM.NS", "JBCHEPHM.NS", "ERIS.NS"
]


def get_nifty_500_symbols(use_online_fetch: bool = True) -> List[str]:
    """
    Retrieves the list of Nifty 500 stock tickers formatted for yfinance (.NS suffix).
    Attempts to download from official NSE CSV source if enabled, defaulting to fallback list.
    """
    if use_online_fetch:
        try:
            url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                from io import StringIO
                df = pd.read_csv(StringIO(res.text))
                if "Symbol" in df.columns:
                    symbols = [f"{sym.strip()}.NS" for sym in df["Symbol"].dropna().unique()]
                    if len(symbols) >= 100:
                        logger.info(f"Successfully fetched {len(symbols)} Nifty 500 tickers from NSE.")
                        return symbols
        except Exception as e:
            logger.warning(f"Failed to fetch live Nifty 500 list: {e}. Using fallback list.")

    # Return deduplicated fallback list
    seen = set()
    deduped = []
    for s in NIFTY_500_FALLBACK:
        if s not in seen:
            seen.add(s)
            deduped.append(s)
    return deduped


def fetch_stock_data(
    symbol: str, period: str = "1y", interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """
    Fetches historical OHLCV data for a single stock using yfinance.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty or len(df) < 20:
            return None
        
        # Ensure column names are standardized
        df.columns = [col.capitalize() for col in df.columns]
        
        # Ensure standard OHLCV presence
        req_cols = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in df.columns for col in req_cols):
            return None

        # Add Turnover (Close * Volume in INR)
        df["Turnover"] = df["Close"] * df["Volume"]
        return df
    except Exception as e:
        logger.error(f"Error downloading data for {symbol}: {e}")
        return None


def fetch_bulk_stock_data(
    symbols: List[str], period: str = "1y", interval: str = "1d"
) -> Dict[str, pd.DataFrame]:
    """
    Fetches stock data for a list of symbols sequentially or in batch.
    Returns a dictionary mapping symbol -> DataFrame.
    """
    stock_map = {}
    for sym in symbols:
        df = fetch_stock_data(sym, period=period, interval=interval)
        if df is not None and not df.empty:
            stock_map[sym] = df
    return stock_map
