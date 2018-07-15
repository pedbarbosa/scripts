#!/bin/bash
INTERVAL=$1
SOURCE=~/downloads/
DESTINATION=~/unpack/
EXTENSION="*.mkv"

cd
SEARCH=$(find ${SOURCE} -type f -name ${EXTENSION} -cmin -${INTERVAL} | sort | xargs -i basename "{}")
SEARCH_EXIT=$?

if [[ "$SEARCH_EXIT" == 0 ]]
then
    echo
    echo "Found the files listed below:"
    echo
    echo "$SEARCH"
    echo
    read -r -p "Would you like to copy these files to $DESTINATION ? [y/N] " response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]
    then
        echo
        echo "Copying files to $DESTINATION..."
        find ${SOURCE} -type f -name ${EXTENSION} -cmin -${INTERVAL} | xargs -i cp {} ${DESTINATION}
        if [[ "$?" == 0 ]]; then
            echo "Successfully copied files."
        else
            echo "Copy process failed."
        fi
        echo
        echo "Listing contents of $DESTINATION:"
        ls -l ${DESTINATION}
    fi
else
    echo "There were no $EXTENSION files created within the last $INTERVAL minutes."
fi

cd -
