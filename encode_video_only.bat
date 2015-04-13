@ECHO OFF
SET ffmpeg=C:\Program Files\ffmpeg\bin\ffmpeg.exe
SET source=D:\Video\encode
SET destination=D:\Video\incoming
SET rubbish=D:\Video\rubbish
SET options=-vcodec libx264 -crf 20 -preset slow -acodec copy -scodec copy

for %%i in (%source%\*.*) do (
    "%ffmpeg%" -i "%%i" %options% "%destination%\%%~ni.mkv"
)
if %errorlevel% == 0 (
    move "%destination%\%%~ni.mkv" %rubbish%
) else (
    echo Encoding failed :(
)