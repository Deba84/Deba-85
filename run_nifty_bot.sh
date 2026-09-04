#!/bin/bash
# Nifty 500 Liquidity Bot Continuous Runner Script (NSE India)

INTERVAL_MINUTES=15

echo "Starting Nifty 500 Liquidity Sweep & Fundamental Bot..."
echo "Scanning NSE Nifty 500 stocks every ${INTERVAL_MINUTES} minutes with Telegram alerts enabled..."

python3 cli.py --double-confirmation --telegram --interval ${INTERVAL_MINUTES} --export
