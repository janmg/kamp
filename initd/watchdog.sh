#!/bin/bash
SERVICE="zomerkamp"
URL="https://zomerkamp.janmg.com/static/polaris.png"
LOGFILE="/var/log/service-monitor.log"

# Ensure log file exists and is writable
touch "$LOGFILE" 2>/dev/null

# Check if service is started in OpenRC
if ! rc-service "$SERVICE" status | grep -q "started"; then
    echo "$(date): $SERVICE OpenRC status is not 'started'. Restarting..." >> "$LOGFILE"
    rc-service "$SERVICE" restart
    exit 0
fi

# Check if the web service is actually responding
# -s: silent, -f: fail on 4xx/5xx, --head: only fetch headers
if ! curl -s -f --head "$URL" > /dev/null; then
    echo "$(date): $SERVICE health check failed (URL: $URL). Restarting..." >> "$LOGFILE"
    rc-service "$SERVICE" restart
fi
