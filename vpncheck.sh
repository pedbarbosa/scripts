#!/usr/bin/env bash
CONTAINER=nordvpn
SERVICE=vpn
LOGFILE=/tmp/vpn_seedbox.log
STATEFILE=/tmp/vpn_last_check.txt

message () { echo ">> [`date '+%F %T'`] $1" >> ${LOGFILE}; }
dir_check_fail () { message "Failed to change directory to '$DIR', aborting ..." && exit 1; }
service_check_fail () { message "Service '$SERVICE' is unavailable, aborting ..." && exit 1; }

# Check if container service is running
if ! docker inspect $CONTAINER >/dev/null 2>&1; then
    service_check_fail
fi

# Check if we have a last_state file
if [ ! -f "$STATEFILE" ]; then
    message "Could not find previous state file, marking previous state as 'unknown'"
    echo "UNKNOWN" > "$STATEFILE"
    exit 0
else
    LAST_STATE=$(cat $STATEFILE)
fi

# Determine container state
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
STATE=`docker inspect $CONTAINER | jq -r '.[].State'`
STATUS=`echo $STATE | jq -r '.Health.Status'`

# Determine if stack needs to be restarted
if [ $STATUS == "starting" ]; then
    message "Service is starting, updating last state as starting ..."
    echo "STARTING" > "$STATEFILE"
elif [ $STATUS == "unhealthy" ]; then
    message "Service is offline!"
    if [ $LAST_STATE == "UNHEALTHY" ]; then
        cd $DIR || dir_check_fail

        message "Taking docker stack down ..." \
            && docker-compose down >>${LOGFILE} 2>&1 \
            && message "Bringing docker stack back up ..." \
            && docker-compose up -d >>${LOGFILE} 2>&1 \
            && message "Docker stack is starting up."
        cd - >/dev/null
    else
        message "Last state was healthy, updating last state file to unhealthy ..."
        echo "UNHEALTHY" > "$STATEFILE"
    fi
else
    message "Service is healthy"
    echo "HEALTHY" > "$STATEFILE"
fi
