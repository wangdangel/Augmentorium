@echo off
REM === Augmentorium Setup Script ===
REM This script checks for Python, Node.js, and NSSM, installs dependencies, and registers Supervisor as a Windows service.

REM --- Check for Administrator Privileges ---
openfiles >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo This script must be run as Administrator.
    echo Please right-click and select 'Run as administrator'.
    pause
    exit /b 1
)

REM === Check for Python ===
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed.
    echo Downloading and installing Python...
    set "PYTHON_URL=https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe"
    set "PYTHON_EXE=%TEMP%\python.exe"
    powershell -Command "Invoke-WebRequest -Uri %PYTHON_URL% -OutFile '%PYTHON_EXE%'"
    start /wait "%PYTHON_EXE%" /quiet InstallAllUsers=1 PrependPath=1
    del "%PYTHON_EXE%"
)

REM === Check for Node.js ===
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Node.js is not installed.
    echo Downloading and installing Node.js...
    set "NODE_URL=https://nodejs.org/dist/v16.13.1/node-v16.13.1-x64.msi"
    set "NODE_MSI=%TEMP%\node.msi"
    powershell -Command "Invoke-WebRequest -Uri %NODE_URL% -OutFile '%NODE_MSI%'"
    start /wait msiexec /i "%NODE_MSI%" /quiet
    del "%NODE_MSI%"
)

REM === (Optional) Create/activate virtual environment ===
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate

REM === Install dependencies ===
pip install --upgrade pip
pip install -r requirements.txt

REM === Ensure Supervisor is installed ===
pip show supervisor >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    pip install supervisor
)

REM === Check for NSSM and install if missing ===
where nssm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo NSSM not found, downloading and installing...
    set "NSSM_URL=https://nssm.cc/release/nssm-2.24.zip"
    set "NSSM_ZIP=%TEMP%\nssm.zip"
    set "NSSM_DIR=%TEMP%\nssm_extract"
    set "NSSM_DEST=C:\nssm"

    powershell -Command "Invoke-WebRequest -Uri %NSSM_URL% -OutFile '%NSSM_ZIP%'"
    if exist "%NSSM_DIR%" rmdir /s /q "%NSSM_DIR%"
    mkdir "%NSSM_DIR%"
    powershell -Command "Expand-Archive -Path '%NSSM_ZIP%' -DestinationPath '%NSSM_DIR%'"
    if not exist "%NSSM_DEST%" mkdir "%NSSM_DEST%"
    copy /Y "%NSSM_DIR%\nssm-2.24\win64\nssm.exe" "%NSSM_DEST%\nssm.exe"
    if not exist "%NSSM_DEST%\nssm.exe" copy /Y "%NSSM_DIR%\nssm-2.24\win32\nssm.exe" "%NSSM_DEST%\nssm.exe"
    powershell -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';C:\\nssm', 'Machine')"
    del "%NSSM_ZIP%"
    rmdir /s /q "%NSSM_DIR%"
    set PATH=%PATH%;C:\nssm
)

REM Now nssm should be available
where nssm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo NSSM installation failed. Please install manually from https://nssm.cc/download
    pause
    exit /b 1
)

REM === Register Supervisor as a Windows service ===
nssm stop AugmentoriumSupervisor >nul 2>nul
nssm remove AugmentoriumSupervisor confirm >nul 2>nul
nssm install AugmentoriumSupervisor ".venv\Scripts\supervisord.exe" "-c supervisord.conf"
nssm set AugmentoriumSupervisor AppDirectory "%CD%"
nssm set AugmentoriumSupervisor DisplayName "Augmentorium Supervisor Service"
nssm set AugmentoriumSupervisor Start SERVICE_AUTO_START
nssm start AugmentoriumSupervisor

echo.
echo Setup complete!
echo The Augmentorium backend, indexer, and frontend will now be managed by Supervisor as a Windows service.
pause
