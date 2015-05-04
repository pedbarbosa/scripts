#!/bin/bash
LOCKFILE=/tmp/mover.lock
CONFIGFILE=~/.mover

# Check if the script is already running
if [[ -e ${LOCKFILE} ]] && kill -0 `cat ${LOCKFILE}`; then
    echo "Error: Lock file present at $LOCKFILE"
    exit
fi

# Create lock file
trap "rm -f ${LOCKFILE}; exit" INT TERM EXIT
echo $$ > ${LOCKFILE}

# Check configuration file
if [[ ! -e ${CONFIGFILE} ]]; then
    echo "Error: Config file missing"
    exit 1
else
    source ${CONFIGFILE}
fi

# Start logging
echo "----------------------------" >> $LOGFILE
echo `date` >> $LOGFILE
echo "----------------------------" >> $LOGFILE

if [[ ${RSYNC_ENABLED} -eq "TRUE" ]]; then
    echo "Invoking rsync..." >> $LOGFILE
    rsync -av --append --remove-source-files $RSYNC_SOURCE $SOURCE >> $LOGFILE
fi

# Check if remote computer is available
if [[ ! -d $REMOTEDIR ]]; then
    echo "Remote computer not available"
    exit 1
fi

COUNTER=0
for FILENAME in $(find "$SOURCE/" -maxdepth 1 -type f); do
    FILESIZE="$(stat -c %s $FILENAME)"
    sleep 2
    if [[ $FILESIZE -eq "$(stat -c %s $FILENAME)" ]]; then
        if [[ $FILENAME == *"at.midnight."* ]]; then
            NEWNAME="$(echo $FILENAME | sed -r 's/\.([0-9]{2})([0-9]{2})([0-9]{2})/\.20\1\.\2.\3/g')"
            mv "$FILENAME" "$NEWNAME"
            FILENAME=$NEWNAME
        fi
        echo "Moving file $FILENAME" >> $LOGFILE
        mv "$FILENAME" "$DESTINATION/" && let COUNTER+=1
    fi
done

echo "Moved $COUNTER items" >> $LOGFILE
