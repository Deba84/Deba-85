import os
import json
import logging
import requests
import pandas as pd
from tabulate import tabulate
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def format_ascii_table(results: List[Dict[str, Any]], top_n: int = 15) -> str:
    """
    Formats Nifty 500 scanner results into a clean ASCII table.
    """
    if not results:
        return "No liquidity signals detected in Nifty 500."

    subset = results[:top_n]
    table_data = []

    for item in subset:
        signals_str = ", ".join(item.get("signals", [])) if item.get("signals") else "NEUTRAL"
        sym = item.get("symbol", "").replace(".NS", "")
        close_val = item.get("close", 0.0)
        close_str = f"₹{close_val:,.2f}"

        turnover_cr = item.get("turnover_cr", 0.0)
        turnover_str = f"₹{turnover_cr:.1f} Cr"

        # Double confirmation indicator
        is_double_conf = "✅ Yes" if item.get("double_confirmation") else "❌ No"

        table_data.append([
            sym,
            close_str,
            f"{item.get('vol_spike_ratio', 1.0)}x",
            turnover_str,
            item.get("liquidity_score", 0.0),
            is_double_conf,
            signals_str
        ])

    headers = ["NSE Symbol", "Close Price", "Vol Spike", "Turnover", "Score", "Double Conf", "Liquidity Signals"]
    return tabulate(table_data, headers=headers, tablefmt="grid")


def export_scan_results(
    results: List[Dict[str, Any]],
    output_dir: str = "reports",
    prefix: str = "nifty500_liquidity"
) -> Dict[str, str]:
    """
    Exports scanner results to CSV and JSON files in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"{prefix}_{timestamp}.csv")
    json_path = os.path.join(output_dir, f"{prefix}_{timestamp}.json")

    # Save CSV
    if results:
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)

    # Save JSON
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Nifty 500 results exported to {csv_path} and {json_path}")
    return {"csv": csv_path, "json": json_path}


def send_telegram_alert(
    bot_token: str,
    chat_id: str,
    results: List[Dict[str, Any]],
    top_n: int = 10
) -> bool:
    """
    Sends Nifty 500 liquidity sweep alerts with fundamental double confirmation to Telegram.
    """
    if not bot_token or not chat_id:
        logger.warning("Telegram bot_token or chat_id missing. Skipping Telegram notification.")
        return False

    if not results:
        message = "🤖 *Nifty 500 Liquidity Bot*\n\nNo high liquidity sweep opportunities detected right now."
    else:
        top_items = results[:top_n]
        lines = ["🤖 *NIFTY 500 LIQUIDITY SWEEP & FUNDAMENTAL BOT*\n"]
        lines.append(f"🔥 *Top {len(top_items)} Nifty 500 Stock Signals*\n")

        for idx, item in enumerate(top_items, 1):
            sym = item.get("symbol", "").replace(".NS", "")
            close = item.get("close", 0.0)
            vol_ratio = item.get("vol_spike_ratio", 1.0)
            turnover = item.get("turnover_cr", 0.0)
            score = item.get("liquidity_score", 0.0)
            sigs = ", ".join(item.get("signals", []))
            double_conf = item.get("double_confirmation", False)

            price_str = f"₹{close:,.2f}"

            double_conf_badge = "🎯 *DOUBLE CONFIRMED (Sweep + Strong Fundamentals)*" if double_conf else "⚡ *Technical Sweep Signal*"

            fund_info = ""
            if "fundamentals" in item and item["fundamentals"]:
                f = item["fundamentals"]
                pe = f.get("pe_ratio", "N/A")
                roe = f.get("roe_pct", "N/A")
                mcap = f.get("market_cap_cr", "N/A")
                fund_info = f"\n   📊 *Fundamentals:* P/E: {pe} | ROE: {roe}% | MCap: ₹{mcap} Cr"

            swept_level = item.get("swept_level")
            sweep_level_str = f"\n   🎯 *Swept Level:* ₹{swept_level:,.2f}" if swept_level else ""

            lines.append(
                f"*{idx}. {sym}* | Liquidity Score: *{score}*\n"
                f"   {double_conf_badge}\n"
                f"   💵 Price: {price_str} | Vol Spike: *{vol_ratio}x* | Turnover: ₹{turnover:.1f} Cr{sweep_level_str}{fund_info}\n"
                f"   ⚡ Signals: `{sigs}`\n"
            )

        lines.append("\n_Nifty 500 Liquidity Scanner Bot (NSE India)_")
        message = "\n".join(lines)

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            logger.info("Successfully sent Nifty 500 Telegram alert.")
            return True
        else:
            logger.error(f"Failed to send Telegram alert. Status code: {res.status_code}, Response: {res.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")
        return False


def send_discord_alert(
    webhook_url: str,
    results: List[Dict[str, Any]],
    top_n: int = 10
) -> bool:
    """
    Sends Nifty 500 scanner alerts to Discord channel via Webhook.
    """
    if not webhook_url:
        logger.warning("Discord webhook_url missing. Skipping Discord notification.")
        return False

    table_str = format_ascii_table(results, top_n=top_n)
    content = f"**Nifty 500 Indian Stock Liquidity Bot Report**\n```\n{table_str}\n```"

    payload = {"content": content}
    try:
        res = requests.post(webhook_url, json=payload, timeout=10)
        if res.status_code in [200, 204]:
            logger.info("Successfully sent Discord webhook alert.")
            return True
        else:
            logger.error(f"Failed to send Discord webhook alert. Status code: {res.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error sending Discord webhook alert: {e}")
        return False
