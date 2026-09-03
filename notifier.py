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
    Formats the top_n scanner results into a clean ASCII table.
    """
    if not results:
        return "No liquidity signals detected."

    subset = results[:top_n]
    table_data = []

    for item in subset:
        signals_str = ", ".join(item.get("signals", [])) if item.get("signals") else "NEUTRAL"
        sym = item.get("symbol", "").replace(".NS", "")
        close_val = item.get("close", 0.0)

        # Format close price nicely depending on scale
        if close_val < 0.01:
            close_str = f"{close_val:.6f}"
        elif close_val < 1.0:
            close_str = f"{close_val:.4f}"
        else:
            close_str = f"{close_val:,.2f}"

        # Currency / Turnover formatting
        turnover_cr = item.get("turnover_cr", 0.0)
        if sym.endswith("-USD") or "USD" in sym:
            # Turnover in USD Millions
            turnover_usd_m = turnover_cr * (1e7 / 1e6)  # convert back from Cr (10M) to M
            if turnover_usd_m >= 1000:
                turnover_str = f"${turnover_usd_m/1000:.2f}B"
            else:
                turnover_str = f"${turnover_usd_m:.1f}M"
        else:
            turnover_str = f"₹{turnover_cr:.1f} Cr"

        table_data.append([
            sym,
            close_str,
            f"{item.get('vol_spike_ratio', 1.0)}x",
            turnover_str,
            item.get("liquidity_score", 0.0),
            signals_str
        ])

    headers = ["Symbol", "Close", "Vol Spike", "Turnover", "Score", "Liquidity Signals"]
    return tabulate(table_data, headers=headers, tablefmt="grid")


def export_scan_results(
    results: List[Dict[str, Any]],
    output_dir: str = "reports",
    prefix: str = "nifty_liquidity"
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

    logger.info(f"Results exported to {csv_path} and {json_path}")
    return {"csv": csv_path, "json": json_path}


def send_telegram_alert(
    bot_token: str,
    chat_id: str,
    results: List[Dict[str, Any]],
    top_n: int = 10
) -> bool:
    """
    Sends formatted scanner alerts to a Telegram chat using Telegram Bot API.
    """
    if not bot_token or not chat_id:
        logger.warning("Telegram bot_token or chat_id missing. Skipping Telegram notification.")
        return False

    if not results:
        message = "🤖 *Nifty 500 Liquidity Scanner*\n\nNo high liquidity signals detected today."
    else:
        top_items = results[:top_n]
        lines = ["🤖 *NIFTY 500 MAJOR LIQUIDITY BOT REPORT*\n"]
        lines.append(f"🔥 *Top {len(top_items)} Liquidity Opportunities*\n")

        for idx, item in enumerate(top_items, 1):
            sym = item.get("symbol", "").replace(".NS", "")
            close = item.get("close", 0.0)
            vol_ratio = item.get("vol_spike_ratio", 1.0)
            turnover = item.get("turnover_cr", 0.0)
            score = item.get("liquidity_score", 0.0)
            sigs = ", ".join(item.get("signals", []))

            if close < 0.01:
                price_str = f"${close:.6f}" if "USD" in sym or "-" in sym else f"₹{close:.6f}"
            elif close < 1.0:
                price_str = f"${close:.4f}" if "USD" in sym or "-" in sym else f"₹{close:.4f}"
            else:
                price_str = f"${close:,.2f}" if "USD" in sym or "-" in sym else f"₹{close:,.2f}"

            lines.append(
                f"*{idx}. {sym}* | Score: *{score}*\n"
                f"   💵 Price: {price_str} | Vol Spike: *{vol_ratio}x*\n"
                f"   ⚡ Signals: `{sigs}`\n"
            )

        lines.append("\n_Scanned via Nifty 500 Major Liquidity Scanner Bot_")
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
            logger.info("Successfully sent Telegram alert.")
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
    Sends formatted scanner alerts to a Discord channel via Webhook.
    """
    if not webhook_url:
        logger.warning("Discord webhook_url missing. Skipping Discord notification.")
        return False

    table_str = format_ascii_table(results, top_n=top_n)
    content = f"**Nifty 500 Major Liquidity Bot Report**\n```\n{table_str}\n```"

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
