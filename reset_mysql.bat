@echo off
net stop MySQL80
timeout /t 2 /nobreak > nul
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --skip-grant-tables --user=mysql --console --init-file="C:\Users\admin\Documents\nashlibrary\reset_password.sql"
net start MySQL80