#!/bin/bash
#
# diskbackup - hardlink based rsync incremental backup
#
# Use the two variables below to define the hostname and the backup target
backup_name=`echo $HOSTNAME | cut -d "." -f1`
backup_volume="/backup"

backup_log="/var/log/diskbackup.log"
backup_debug="$backup_volume/debug.log"
backup_instance=`date +%Y%m%d_%H%M`
backup_dir="$backup_volume/$backup_name.$backup_instance"

echo -e "\n-----------------------\n| `date +%Y-%m-%d\ %H:%M:%S` |\n-----------------------" >> $backup_log 

clock () { echo ">> [`date +%H:%M:%S`] "; }

pidcheck=$(ps aux | grep [r]sync | wc -l)

if [ $pidcheck -gt 0 ]
	then
		echo `clock`"Suspending, rsync already running" >> $backup_log
	else if [ -d $backup_volume ]
		then
			echo `clock`"Starting backup to $backup_dir" >> $backup_log
            backup_previous=`ls -d1 $backup_volume/$backup_name.* | sort -n | tail -1`
			if [ $backup_previous ]
				then
					echo `clock`"Using $backup_previous for hardlinks" >> $backup_log
					#rsync -a --stats --delete --delete-excluded --exclude-from=$backup_volume/$backup_name\_exclude --link-dest=$backup_previous --log-file=$backup_debug / $backup_dir >> $backup_log 2>> $backup_log
					rsync -a --stats --delete --delete-excluded --exclude-from=$backup_volume/$backup_name\_exclude --link-dest=$backup_previous / $backup_dir >> $backup_log 2>> $backup_log
					rsync_exit=$?
					if [ "$rsync_exit" -ne 0 ]
                        then
                            echo `clock`"Rsync failed with error code $rsync_exit, backup $backup_dir may be corrupt" >> $backup_log
                        else
                            echo `clock`"Rsync finished successfully" >> $backup_log
                    fi
				else
					echo `clock`"Creating new full backup set" >> $backup_log
					#rsync -a --stats --delete --delete-excluded --exclude-from=$backup_volume/$backup_name\_exclude --log-file=$backup_debug / $backup_dir >> $backup_log 2>> $backup_log
					rsync -a --stats --delete --delete-excluded --exclude-from=$backup_volume/$backup_name\_exclude / $backup_dir >> $backup_log 2>> $backup_log
					rsync_exit=$?
					if [ "$rsync_exit" -ne 0 ]; then echo `clock`"Rsync failed with error code $rsync_exit, backup $backup_dir may be corrupt" >> $backup_log; fi
			fi

            # Clean up directories
            for i in `find $backup_volume/$backup_name.* -maxdepth 0 -type d`
            do
                date_folder=`echo $i | cut -d "." -f 2 | cut -d "_" -f 1`
                if [ $date_folder -ne `date +%Y%m%d` -a $date_folder -ne `date -v-1d +%Y%m%d` ]; then
                    num_folders=(`find $backup_volume/$backup_name.$date_folder* -maxdepth 0 -type d | wc -l` / 1)
                    if [ $num_folders -gt 1 ]; then
                        echo `clock`"Clean up: Date $date_folder has $num_folders backups, deleting $i" >> $backup_log
                        rm -rf $i
                        echo `clock`"Clean up: Backup $i removed" >> $backup_log
                    fi
                fi
            done

		else
			echo `clock`"Unable to run backup, target disk unavailable" >> $backup_log
	fi
fi
