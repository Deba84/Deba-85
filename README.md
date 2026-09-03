# Nifty 500 Major Liquidity Scanner & Bot 🚀

An institutional-grade **Nifty 500 Major Liquidity Bot and Scanner** written in Python. This tool scans the Indian Stock Market (Nifty 500 constituents) for major institutional liquidity footprints, volume spikes, smart money liquidity sweeps (ICT / SMC style), and liquidity pool zones.

---

## ⚡ Key Features

1. **Nifty 500 Ticker Management**: Automatically fetches the official Nifty 500 index constituents from NSE India, with built-in fallbacks.
2. **Smart Money Liquidity Sweeps (ICT/SMC)**:
   - **Bullish Liquidity Sweep (Sell-side Liquidity Grab)**: Identifies price sweeps below key swing lows or Equal Lows (EQL) followed by rejection wicks and close recoveries.
   - **Bearish Liquidity Sweep (Buy-side Liquidity Grab)**: Identifies price sweeps above key swing highs or Equal Highs (EQH) followed by rejection wicks and close rejections.
3. **Major Volume & Turnover Spikes**: Detects institutional accumulation/distribution when volume exceeds 2.5x - 5.0x the 20-period Simple Moving Average (SMA) alongside heavy turnover (in Crore INR).
4. **Order Block & Liquidity Pool Detection**: Identifies Equal Highs (EQH) and Equal Lows (EQL) clusters where resting buy-stop and sell-stop orders reside.
5. **Multi-Threaded Parallel Execution**: Concurrent multi-threading scans Nifty 500 stock data in seconds.
6. **Pluggable Notifications & Reports**:
   - **Telegram Bot**: Sends real-time Markdown formatted alerts to your Telegram chat or channel.
   - **Discord Webhook**: Sends alerts to Discord channels with formatted ASCII tables.
   - **JSON / CSV Exporter**: Generates structured reports in `reports/`.

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   cd nifty500-liquidity-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📊 Quick Start / CLI Usage

Scan the market with default settings (Daily interval, Top 15 output):
```bash
python main.py
```

### Advanced Examples:

- **Filter by Specific Signal (e.g. Bullish Liquidity Sweeps)**:
  ```bash
  python main.py --signal BULLISH_LIQUIDITY_SWEEP
  ```

- **Scan Specific Stock Symbols**:
  ```bash
  python main.py --symbol RELIANCE,TCS,HDFCBANK,INFY
  ```

- **Filter by Minimum Liquidity Score & Export Reports**:
  ```bash
  python main.py --min-score 50 --export
  ```

- **Intraday Timeframe Scan (e.g. 15-minute or 1-hour)**:
  ```bash
  python main.py --timeframe 15m --period 1mo
  ```

- **Trigger Telegram & Discord Alerts**:
  ```bash
  python main.py --telegram --discord --export
  ```

---

## ⚙️ Configuration (`config.json`)

Customize parameters in `config.json`:

```json
{
  "scan_settings": {
    "default_timeframe": "1d",
    "lookback_period": "1y",
    "pivot_window": 5,
    "volume_sma_period": 20,
    "volume_spike_threshold": 2.5,
    "liquidity_grab_wick_ratio": 0.35,
    "min_turnover_cr": 5.0
  },
  "telegram": {
    "enabled": true,
    "bot_token": "8830981258:AAG97T2wBO_66z8GQ4kOdoIgTu-NJvWKEXY",
    "chat_id": "YOUR_TELEGRAM_CHAT_ID"
  },
  "discord": {
    "enabled": false,
    "webhook_url": "YOUR_DISCORD_WEBHOOK_URL"
  },
  "export": {
    "output_dir": "reports",
    "save_csv": true,
    "save_json": true
  }
}
```

---

## 🤖 Setting up Telegram Alerts

1. Talk to `@BotFather` on Telegram to create a new bot and copy the **Bot Token**.
2. Start a chat with your bot or add it to a group/channel.
3. Send a message to your bot, then get your **Chat ID** by visiting:
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Paste `bot_token` and `chat_id` into `config.json`.
5. Run `python main.py --telegram`.

---

## 🧪 Running Unit Tests

To run the automated pytest test suite:
```bash
pytest -v
```

---

## 📄 License

MIT License. Disclaimer: For educational and informational purposes only. Not financial advice.
