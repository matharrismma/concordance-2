@echo off
rem EVERY COPY IS WHOLE (Gen 3 . 1, 2026-10-04) - the desktop NODE pulls the keeping from its known branch
rem (the box, pinned by fingerprint in data\known_branches.json): the seal ledger incrementally, the keeping
rem files by hash, every byte re-hashed before it is written. Run by the Windows task "NarrowHighway Node Sync"
rem (daily 23:30); safe by hand. Log: D:\NarrowHighway-Backups\node_sync.log
set REPO=C:\Users\hdven\OneDrive\Documents\Claude\Projects\concordance-2
set LOG=D:\NarrowHighway-Backups\node_sync.log
set PYTHONPATH=%REPO%\src
set CONCORDANCE_DATA_DIR=%REPO%\data
set PYTHONIOENCODING=utf-8
echo === %date% %time% node sync start === >> "%LOG%"
"C:\Users\hdven\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m concordance sync >> "%LOG%" 2>&1
echo === %date% %time% node sync exit %ERRORLEVEL% === >> "%LOG%"
