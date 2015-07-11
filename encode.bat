@ECHO OFF
SET ffmpeg=C:\Program Files\ffmpeg\bin\ffmpeg.exe
SET source=D:\Video\encode
SET destination=D:\Video\incoming
SET rubbish=D:\Video\rubbish
SET options=-vcodec libx264 -crf 23 -preset veryslow -acodec libvo_aacenc -ab 128k -ac 2

for %%i in (%source%\*.*) do (
    "%ffmpeg%" -i "%%i" %options% "%destination%\%%~ni.mkv"
    if %errorlevel% == 0 (
        move "%%i" %rubbish%
    ) else (
        echo Encoding failed, return code %errorlevel% :(
    )
)
