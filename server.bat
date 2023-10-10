@echo off

:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
    IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
>nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config\system"
) ELSE (
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
)

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params= %*
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params:"=""%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
:-------------------------------------- 

:: Get environment variables from .env file
echo Importing environment variables from .env file...
for /f "usebackq tokens=1,2 delims==" %%a in ("%~dp0.env") do (
    set "%%a=%%b"
)

:: UAC prompt will appear next...
echo UAC prompt will appear next...
powershell -Command "Start-Process cmd.exe -Verb runAs -ArgumentList '/c netsh advfirewall firewall add rule name=\"%RULE_NAME%\" dir=in action=allow protocol=TCP localport=%PORT%'"

:: Open TCP port
echo Opening TCP port %RULE_NAME% %PORT%...
netsh advfirewall firewall add rule name='%RULE_NAME% TCP' dir=in action=allow protocol=TCP localport=%PORT%

:: Open UDP port
echo Opening UDP port %RULE_NAME% %PORT%...
netsh advfirewall firewall add rule name='%RULE_NAME% UDP' dir=in action=allow protocol=UDP localport=%PORT%

:: Check if the port is open
echo Checking if the port is open...
powershell -Command "if (Test-NetConnection -ComputerName localhost -Port %PORT%) { echo Port %PORT% is open. } else { echo Port %PORT% is closed. }"

:: Change directory and activate virtual environment
echo Changing directory and activating virtual environment...
call cd ..\KU-Inventory-Lab\
echo venv3 is being activated...
call env3\Scripts\activate.bat

:: Install required packages
echo Installing required packages...
pip install -r requirements.txt

:: Start the server
echo Starting the server...
python server.py

echo Batch file execution completed.
pause
```