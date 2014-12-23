#!/bin/bash
SOURCE=~/unpack
DESTINATION=~/import

for filename in $(find "$SOURCE/" -maxdepth 1 -type f); do
    filesize="$(stat -c %s $filename)"
    sleep 2
    if [[ $filesize -eq "$(stat -c %s $filename)" ]]; then
        mv "$filename" "$DESTINATION/"
    fi
done
