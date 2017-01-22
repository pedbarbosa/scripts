#!/bin/bash
MYSQL_USER=kodi
MYSQL_PASS=kodi
MYSQL_DB=MyVideos99

BACKUP_FILE=/data/backup/kodi-$(date +"%Y-%m-%d_%H-%M").sql
MYSQL_BIN=`which mysqldump`

# TODO: Add error handling and reporting
$MYSQL_BIN -u $MYSQL_USER --password=$MYSQL_PASS -B $MYSQL_DB > $BACKUP_FILE
bzip2 --best $BACKUP_FILE
