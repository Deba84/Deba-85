# 🇮🇳 Nifty 500 Liquidity Sweep & Fundamental Bot (NSE India)

An automated institutional liquidity scanner and Telegram alert bot designed specifically for the **Indian Stock Market (NSE Nifty 500)**.

The bot identifies key **Liquidity Sweeps**, **Near-Sweep Zones (Pre-Sweep setups)**, and **Volume Spikes**, combined with **Fundamental Health Double Confirmation** (Market Cap, P/E Ratio, ROE, Debt-to-Equity).

---

## 🎯 Key Features

1. **Liquidity Sweep Pre-Detection & Active Sweep Engine**:
   - Identifies active **Bullish/Bearish Liquidity Sweeps** (dips/pierces below key swing lows/highs with long wicks).
   - Identifies **Near-Sweep Zones** (stocks trading within 1.5% of key liquidity pools before sweeping).
   - Detects **Equal Highs (EQH) & Equal Lows (EQL)** liquidity pools.

2. **Fundamental Double Confirmation**:
   - Evaluates financial metrics using `yfinance`:
     - **Market Cap**: Minimum ₹500 Cr (Large / Mid Cap Safety).
     - **P/E Ratio**: Fair valuation screening (P/E ≤ 75).
     - **ROE (%)**: Strong profitability (ROE ≥ 8%).
     - **Debt-to-Equity**: Healthy solvency (D/E ≤ 2.5).
   - Flags stocks with **🎯 DOUBLE CONFIRMED** status when both technical liquidity sweep and strong fundamental health are present.

3. **Automated Telegram Alerts**:
   - Sends real-time formatted notifications to Telegram chats/channels with price, volume spike, swept levels, and fundamental metrics badges.

4. **Multi-Threaded NSE Nifty 500 Scanner**:
   - Scans all Nifty 500 equities concurrently with custom timeframe intervals (`1d`, `1h`, `15m`).

---

## 🚀 Quick Start & Usage

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configure Telegram (Optional)
Edit `config.json`:
```json
{
  "telegram": {
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_TELEGRAM_CHAT_ID"
  }
}
```

### 3. Running Scans

#### A. Double Confirmation Scan (Sweep + Strong Fundamentals)
```bash
python3 cli.py --double-confirmation
```

#### B. Active or Near Liquidity Sweep Zone Scan
```bash
python3 cli.py --sweep-only --top 15
```

#### C. Live Market Automated Scanning (Every 15 Minutes with Telegram Alerts)
```bash
python3 cli.py --double-confirmation --telegram --interval 15
```

#### D. Background Execution Script
```bash
chmod +x run_nifty_bot.sh
./run_nifty_bot.sh > niftybot.log 2>&1 &
```

---

## 🧪 Testing

Run unit tests via `pytest`:
```bash
python3 -m pytest
```
