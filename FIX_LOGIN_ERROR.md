# MySQL Server Setup Instructions

## Problem
Your application is getting a 500 error on login because **MySQL is not running**.

## Error Details
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '127.0.0.1' ([WinError 10061]")
```

## Solution: Start MySQL Service

### Option 1: Using START_MYSQL.bat (Recommended)
1. Navigate to: `c:\Users\admin\Documents\nashlibrary\`
2. Right-click on **`START_MYSQL.bat`**
3. Select **"Run as administrator"**
4. A command window will appear and start the MySQL80 service
5. You should see a message saying the service started successfully

### Option 2: Using Services Management
1. Press `Win + R` to open Run dialog
2. Type: `services.msc`
3. Find **"MySQL80"** in the list
4. Right-click it and select **"Start"**
5. The service should change from "Stopped" to "Running"

### Option 3: Using Command Prompt (Admin)
1. Press `Win + X` and select **"Terminal (Admin)"** or **"Command Prompt (Admin)"`
2. Run this command:
   ```
   net start MySQL80
   ```
3. You should see: "The MySQL80 service is starting."

## Verify MySQL is Running

After starting the service, you can verify it's running by checking:
- Task Manager (look for mysqld.exe process)
- Services management (MySQL80 should show "Running")
- Your application should now work without 500 errors

## Database Details
- **Host:** 127.0.0.1
- **Port:** 3306
- **User:** root
- **Database:** library_system_v2

## After MySQL Starts
1. Go back to your browser and refresh the login page
2. Try logging in again - it should work now
3. The application will connect to the running MySQL database

## Troubleshooting
If MySQL still won't start:
- Make sure you have MySQL 8.0 installed (you do - confirmed)
- Run the command with administrator privileges
- Check Event Viewer for MySQL error messages
- The database data folder exists at: `C:\ProgramData\MySQL\MySQL Server 8.0\Data\`

---

**TL;DR:** Right-click `START_MYSQL.bat` and run as administrator to fix the issue.
