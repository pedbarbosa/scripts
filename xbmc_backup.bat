@ECHO OFF

REM Configurable variables
SET mysql_user="root"
SET mysql_bin="C:\Program Files\MySQL\MySQL Server 5.6\bin"
SET backup_dir="%userprofile%\Google Drive\Backups\MySQL"
SET rar_bin="C:\Program Files\WinRAR\rar.exe"

REM Check for password file
IF NOT EXIST xbmc_backup.pwd (
    ECHO ERROR: Missing password file!
    ECHO Please create a file on script directory called "xbmc_backup.pwd".
    ECHO This file should *ONLY* contain the password for the %mysql_user% MySQL user.
    GOTO :EXIT
)
SET /P mysql_pass=<xbmc_backup.pwd

REM Destination for machines set with YYYY-MM-DD
SET hour=%time: =0%
SET rar_backup=%backup_dir%\xbmc-%date:~0,4%%date:~5,2%%date:~8,2%-%hour:~0,2%%time:~3,2%.sql.rar

%mysql_bin%\mysqldump -u %mysql_user% --password=%mysql_pass% -B mymusic52 myvideos93 > %TEMP%\backup.sql
IF %errorlevel% == 0 (
    %rar_bin% a -m5 -s %rar_backup% %TEMP%\backup.sql
    DEL %TEMP%\backup.sql
) ELSE ECHO MySQL dump failed.

:EXIT
