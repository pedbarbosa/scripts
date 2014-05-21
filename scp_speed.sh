#!/bin/bash
USAGE="$0 destination"
if [ $# -ne 1 ]
then
    echo $USAGE
	exit 0
fi

TARGET=$1
TMPFILE="/tmp/transfer"
#LOGFILE="report"

for i in {1..2}
do
	COPYFILE="SpeedTest_`date +%Y%m%d_%H%M_%S`.tmp"
	dd if=/dev/urandom of=/tmp/$COPYFILE bs=10m count=1 2>/dev/null

	scp -v /tmp/$COPYFILE $TARGET >&$TMPFILE
	echo "`date +%Y%m%d_%H%M` UP `grep 'Bytes per second' $TMPFILE | awk '{ print $5 }'`"
	sleep 2
	scp -v $TARGET/$COPYFILE /tmp >&$TMPFILE
	echo "`date +%Y%m%d_%H%M` DN `grep 'Bytes per second' $TMPFILE | awk '{ print $7 }'`"
	sleep 5

	rm /tmp/$COPYFILE
done
