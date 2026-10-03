@echo off
rem THE ARK, weekly — pull the box's newest data tar + the shards onto the 12 TB drive and verify them
rem (tools/ark_pull.sh in concordance-2). Run by the Windows task "NarrowHighway Ark Pull"; safe by hand.
set REPO=C:\Users\hdven\OneDrive\Documents\Claude\Projects\concordance-2
set LOG=D:\NarrowHighway-Backups\hetzner\ark_pull.log
echo === %date% %time% ark pull start === >> "%LOG%"
"C:\Program Files\Git\bin\bash.exe" -lc "cd '%REPO%' && sh tools/ark_pull.sh shards" >> "%LOG%" 2>&1
echo === %date% %time% ark pull exit %ERRORLEVEL% === >> "%LOG%"
