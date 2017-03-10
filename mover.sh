#!/bin/bash
LOCKFILE=/tmp/mover.lock
CONFIGFILE=~/.mover

# Check configuration file
if [[ ! -e ${CONFIGFILE} ]]; then
    echo "Error: Config file missing. Copy mover.cfg to ~/.mover and configure as required."
    exit 1
else
    source ${CONFIGFILE}
fi

clock () { echo ">> [`date +%H:%M:%S`] "; }

# Check if the script is already running
if [[ -e ${LOCKFILE} ]] && kill -0 `cat ${LOCKFILE}`; then
    echo `clock`"Refusing to run, found lock file at $LOCKFILE" >> $LOGFILE
    exit 1
fi

# Create lock file
trap "rm -f ${LOCKFILE}; exit" INT TERM EXIT
echo $$ > ${LOCKFILE}
echo `clock`"Application successfully started" >> $LOGFILE

# Check if rsync is enabled
if [[ ${RSYNC_ENABLED} -eq "TRUE" ]]; then
    # Check if any orphaned rsync processes are running
    pidcheck=$(ps aux | grep [r]sync | wc -l)

    if [ $pidcheck -gt 0 ]; then
        echo `clock`"Suspending, rsync already running" >> $LOGFILE
        exit 1
    fi

    # Rsync execution
    echo `clock`"Invoking rsync..." >> $LOGFILE
    rsync -av --append --remove-source-files $RSYNC_SOURCE $SOURCE >> $LOGFILE
    rsync_exit=$?
    if [ "$rsync_exit" -ne 0 ]; then
        echo `clock`"Rsync exited with non-zero code, aborting script" >> $LOGFILE
        exit 1
    fi
fi

# Check if remote computer is available
if [[ ! -d $REMOTEDIR ]]; then
    echo `clock`"Remote computer not available" >> $LOGFILE
    exit 1
fi

# Move files to final location
COUNTER=0
SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
for FILENAME in $(find "$SOURCE/" -maxdepth 1 -type f); do
    FILESIZE="$(stat -c %s $FILENAME)"
    sleep 2
    if [[ $FILESIZE -eq "$(stat -c %s $FILENAME)" ]]; then
        echo `clock`"Moving file $FILENAME to $DESTINATION..." >> $LOGFILE
        mv "$FILENAME" "$DESTINATION/" && let COUNTER+=1
    fi
done
IFS=$SAVEIFS

echo `clock`"Moved $COUNTER items" >> $LOGFILE
