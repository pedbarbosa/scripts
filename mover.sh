#!/bin/bash
SOURCE=~/unpack
DESTINATION=~/import
REMOTEDIR=/video/TV
COUNTER=0

# Check if remote computer is available
if [[ ! -d $REMOTEDIR ]]; then
    exit 1
fi

for FILENAME in $(find "$SOURCE/" -maxdepth 1 -type f); do
    FILESIZE="$(stat -c %s $FILENAME)"
    sleep 2
    if [[ $FILESIZE -eq "$(stat -c %s $FILENAME)" ]]; then
        if [[ $FILENAME == *"at.midnight."* ]]; then
            NEWNAME="$(echo $FILENAME | sed -r 's/\.([0-9]{2})([0-9]{2})([0-9]{2})/\.20\1\.\2.\3/g')"
            mv "$FILENAME" "$NEWNAME"
            FILENAME=$NEWNAME
        fi
        mv "$FILENAME" "$DESTINATION/" && let COUNTER+=1
    fi
done

#if [[ $COUNTER -ne 0 ]]; then
#    echo "Moved $COUNTER items"
#fi
