#!/usr/bin/env bash

# Set collectd RRD path
SCAN_PATH=/var/lib/collectd/rrd/router

# Set maximum RRD file age, in minutes
MAX_AGE=10

LAST_MODIFIED=$(find $SCAN_PATH -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")
LAST_TIMESTAMP=$(date +%s -r $LAST_MODIFIED)

CURRENT_TIME=$(date +%s)
DELTA=$((CURRENT_TIME-LAST_TIMESTAMP))

SECONDS=$(($MAX_AGE*60))
if [[ ${DELTA} -gt ${SECONDS} ]]; then
    echo "Newest update in '${SCAN_PATH}' was ${DELTA} seconds ago, which exceeds the threshold of ${SECONDS}."
    echo "Restarting 'collectd' locally ..."
    sudo systemctl restart collectd
    sleep 1
    echo "Stopping 'collectd' in router ..."
    ssh router '/etc/init.d/collectd stop'
    sleep 1
    echo "Starting 'collectd' in router ..."
    ssh router '/etc/init.d/collectd start'
fi

