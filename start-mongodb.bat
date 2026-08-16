@echo off
echo Starting local MongoDB on 127.0.0.1:27017 (Ctrl+C to stop)...
"C:\Users\laksh\mongodb\mongodb-win32-x86_64-windows-8.3.8\bin\mongod.exe" --dbpath "C:\Users\laksh\mongodb\data\db" --logpath "C:\Users\laksh\mongodb\data\log\mongod.log" --port 27017 --bind_ip 127.0.0.1
echo MongoDB stopped.
pause
