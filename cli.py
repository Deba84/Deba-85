import argparse
import sys
import logging
from typing import List

from scanner import NiftyLiquidityScanner
from notifier import format_ascii_table, export_scan_results, send_telegram_alert, send_discord_alert

def main():
    parser = argparse.ArgumentParser(
        description="Nifty 500 Major Liquidity Bot & Scanner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--market", "-m", default="nifty", choices=["nifty", "crypto", "all"], help="Market universe to scan (nifty, crypto, all)")
    parser.add_argument("--crypto", action="store_true", help="Shortcut to scan top Cryptocurrency pairs")
    parser.add_argument("--timeframe", "-tf", default="1d", help="Candle timeframe interval (e.g., 1d, 1h, 15m, 1wk)")
    parser.add_argument("--period", "-p", default="1y", help="Historical data period (e.g., 1y, 6m, 1m)")
    parser.add_argument("--top", "-n", type=int, default=15, help="Top N opportunities to display")
    parser.add_argument("--min-score", "-s", type=float, default=0.0, help="Minimum Liquidity Score filter (0-100)")
    parser.add_argument("--signal", "-sig", help="Filter by signal name (e.g., BULLISH_LIQUIDITY_SWEEP, MAJOR_VOLUME_SPIKE)")
    parser.add_argument("--symbol", "-sym", help="Specific ticker symbol or comma-separated symbols (e.g. RELIANCE.NS, BTC-USD)")
    parser.add_argument("--sweep-only", action="store_true", help="Filter to show only stocks with active or near liquidity sweeps")
    parser.add_argument("--double-confirmation", "-dc", action="store_true", help="Filter for Double Confirmation (Liquidity Sweep + Strong Fundamentals)")
    parser.add_argument("--workers", "-w", type=int, default=10, help="Number of concurrent threads for scanning")
    parser.add_argument("--export", action="store_true", help="Export scan results to CSV and JSON reports")
    parser.add_argument("--telegram", action="store_true", help="Send alert to Telegram channel/chat")
    parser.add_argument("--discord", action="store_true", help="Send alert to Discord webhook")
    parser.add_argument("--interval", "-i", type=int, default=0, help="Automated scan interval in minutes (0 = run once)")
    parser.add_argument("--config", default="config.json", help="Path to config.json file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose log output")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")

    print("\n=======================================================")
    print("      🚀 NIFTY 500 MAJOR LIQUIDITY BOT & SCANNER       ")
    print("=======================================================\n")

    scanner = NiftyLiquidityScanner(config_path=args.config)

    market = "crypto" if args.crypto else args.market

    # Process custom symbols if provided
    symbols_list = None
    if args.symbol:
        raw_syms = args.symbol.split(",")
        symbols_list = []
        for sym in raw_syms:
            sym = sym.strip().upper()
            if "-" in sym or sym.endswith("USD") or sym.endswith("USDT") or sym.endswith("BTC"):
                if not sym.endswith("-USD") and not "-" in sym and (sym.endswith("USD") or sym.endswith("USDT")):
                    sym = f"{sym[:-3]}-USD" if sym.endswith("USD") else f"{sym[:-4]}-USD"
                symbols_list.append(sym)
            elif not sym.endswith(".NS") and not sym.startswith("^"):
                if market == "crypto":
                    symbols_list.append(f"{sym}-USD")
                else:
                    symbols_list.append(f"{sym}.NS")
            else:
                symbols_list.append(sym)

    import time

    def run_scan_cycle():
        print(f"Scanning {market.upper()} market data... (Interval: {args.timeframe}, Period: {args.period})")
        if args.double_confirmation:
            print("🎯 Double Confirmation Filter Enabled: Requiring Liquidity Sweep + Strong Fundamentals!")
        elif args.sweep_only:
            print("⚡ Sweep Only Filter Enabled: Showing only stocks dipping/piercing liquidity levels!")

        results = scanner.scan_market(
            symbols=symbols_list,
            market=market,
            period=args.period,
            interval=args.timeframe,
            max_workers=args.workers,
            min_score=args.min_score,
            signal_filter=args.signal,
            sweep_only=args.sweep_only,
            double_confirmation_only=args.double_confirmation
        )

        print(f"\nScan completed! Total qualifying symbols found: {len(results)}\n")

        # Render table
        table_output = format_ascii_table(results, top_n=args.top)
        print(table_output)
        print("\n")

        # Export if requested
        if args.export:
            exported = export_scan_results(results)
            print(f"📁 Results saved: CSV -> {exported['csv']} | JSON -> {exported['json']}")

        # Telegram Alert
        if args.telegram:
            telegram_cfg = scanner.config.get("telegram", {})
            bot_token = telegram_cfg.get("bot_token")
            chat_id = telegram_cfg.get("chat_id")

            if not bot_token or not chat_id:
                print("⚠️ Telegram token or chat_id not found in config.json.")
            else:
                success = send_telegram_alert(bot_token, chat_id, results, top_n=args.top)
                if success:
                    print("📱 Telegram alert sent successfully.")
                else:
                    print("❌ Failed to send Telegram alert.")

        # Discord Alert
        if args.discord:
            discord_cfg = scanner.config.get("discord", {})
            webhook_url = discord_cfg.get("webhook_url")

            if not webhook_url:
                print("⚠️ Discord webhook_url not found in config.json.")
            else:
                success = send_discord_alert(webhook_url, results, top_n=args.top)
                if success:
                    print("💬 Discord alert sent successfully.")
                else:
                    print("❌ Failed to send Discord alert.")

    if args.interval > 0:
        print(f"🔄 Automated Mode Active! Scanning every {args.interval} minutes. Press Ctrl+C to stop.\n")
        try:
            while True:
                run_scan_cycle()
                print(f"⏳ Sleeping for {args.interval} minutes until next scan...")
                time.sleep(args.interval * 60)
        except KeyboardInterrupt:
            print("\n🛑 Bot automated scheduling stopped by user.")
    else:
        run_scan_cycle()


if __name__ == "__main__":
    main()
