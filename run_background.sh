#!/usr/bin/env bash
# Script to run the Liquidity Scanner Bot continuously in the background

INTERVAL=${1:-15}
MARKET=${2:-crypto}
LOG_FILE="bot.log"

echo "Starting Liquidity Bot in background (Market: ${MARKET}, Interval: ${INTERVAL} mins)..."
nohup python3 cli.py --market "${MARKET}" --interval "${INTERVAL}" --telegram >> "${LOG_FILE}" 2>&1 &

PID=$!
echo "Bot started successfully with PID: ${PID}"
echo "Log file: ${LOG_FILE}"
echo "To check status: tail -f ${LOG_FILE}"
echo "To stop the bot: kill ${PID} (or pkill -f 'python3 cli.py')"
