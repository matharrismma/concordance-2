@echo off
rem THE DECISION MEMORY, SEALED daily — see seal_memory.sh. Run by the Windows task "NarrowHighway Memory Seal".
"C:\Program Files\Git\bin\bash.exe" -lc "sh /d/NarrowHighway-Backups/seal_memory.sh" >> D:\NarrowHighway-Backups\memory\seal_task.log 2>&1
