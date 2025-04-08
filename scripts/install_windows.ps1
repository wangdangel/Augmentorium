# Installation script for Augmentorium on Windows
# Run as administrator for best results

# Configuration
$AugmentoriumDir = "$env:USERPROFILE\.augmentorium"
$VenvPath = "$AugmentoriumDir\venv"
$TreeSitterDir = "$AugmentoriumDir\tree-sitter-grammars"
$LogsDir = "$AugmentoriumDir\logs"
$BinDir = "$AugmentoriumDir\bin"
$StartupDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"

# Print header
Write-Host "============================================" -ForegroundColor Green
Write-Host "     Augmentorium Installer for Windows     " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param (
        [string]$Command
    )
    try {
        Get-Command $Command -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Check for required commands
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$MissingDeps = $false

if (-not (Test-Command "python")) {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.8 or newer." -ForegroundColor Red
    $MissingDeps = $true
}
else {
    $PythonVersion = (python --version) 2>&1
    Write-Host "Found $PythonVersion" -ForegroundColor Green
}

if (-not (Test-Command "pip")) {
    Write-Host "pip is not installed or not in PATH. Please install pip." -ForegroundColor Red
    $MissingDeps = $true
}

if (-not (Test-Command "git")) {
    Write-Host "git is not installed or not in PATH. Please install git." -ForegroundColor Red
    $MissingDeps = $true
}

if ($MissingDeps) {
    Write-Host "Please install the missing dependencies and run the installer again." -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $AugmentoriumDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
New-Item -ItemType Directory -Path $TreeSitterDir -Force | Out-Null
New-Item -ItemType Directory -Path $BinDir -Force | Out-Null

# Create virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
}
else {
    Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Yellow
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$ActivateScript = "$VenvPath\Scripts\Activate.ps1"
. $ActivateScript

# Install or upgrade Augmentorium
if (-not $args[0]) {
    # No argument, install from PyPI
    Write-Host "Installing Augmentorium from PyPI..." -ForegroundColor Yellow
    pip install --upgrade augmentorium
}
else {
    # Argument provided, install from directory
    Write-Host "Installing Augmentorium from $($args[0])..." -ForegroundColor Yellow
    pip install --upgrade $args[0]
}

# Create Windows Service Wrapper config files
Write-Host "Creating service configuration files..." -ForegroundColor Yellow

# Download NSSM if not present
$NssmPath = "$BinDir\nssm.exe"
if (-not (Test-Path $NssmPath)) {
    Write-Host "Downloading NSSM (Non-Sucking Service Manager)..." -ForegroundColor Yellow
    $NssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $NssmZip = "$env:TEMP\nssm.zip"
    
    Invoke-WebRequest -Uri $NssmUrl -OutFile $NssmZip
    Expand-Archive -Path $NssmZip -DestinationPath "$env:TEMP\nssm" -Force
    Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" -Destination $NssmPath
    Remove-Item $NssmZip
    Remove-Item "$env:TEMP\nssm" -Recurse -Force
}

# Create batch files for services
$IndexerScript = @"
@echo off
call "$VenvPath\Scripts\activate.bat"
augmentorium-indexer --log-level INFO
"@

$ServerScript = @"
@echo off
call "$VenvPath\Scripts\activate.bat"
augmentorium-server --log-level INFO
"@

# Write batch files
$IndexerBatch = "$BinDir\augmentorium-indexer.bat"
$ServerBatch = "$BinDir\augmentorium-server.bat"

Set-Content -Path $IndexerBatch -Value $IndexerScript
Set-Content -Path $ServerBatch -Value $ServerScript

# Create services using NSSM
Write-Host "Creating Windows services..." -ForegroundColor Yellow

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if ($IsAdmin) {
    # Remove existing services if they exist
    & $NssmPath stop AugmentoriumIndexer 2>$null
    & $NssmPath remove AugmentoriumIndexer confirm 2>$null
    
    & $NssmPath stop AugmentoriumServer 2>$null
    & $NssmPath remove AugmentoriumServer confirm 2>$null
    
    # Create indexer service
    & $NssmPath install AugmentoriumIndexer $IndexerBatch
    & $NssmPath set AugmentoriumIndexer DisplayName "Augmentorium Indexer Service"
    & $NssmPath set AugmentoriumIndexer Description "Augmentorium code indexing service"
    & $NssmPath set AugmentoriumIndexer AppStdout "$LogsDir\indexer-output.log"
    & $NssmPath set AugmentoriumIndexer AppStderr "$LogsDir\indexer-error.log"
    & $NssmPath set AugmentoriumIndexer AppRotateFiles 1
    & $NssmPath set AugmentoriumIndexer AppRotateOnline 1
    & $NssmPath set AugmentoriumIndexer AppRotateSeconds 86400
    & $NssmPath set AugmentoriumIndexer Start SERVICE_AUTO_START
    
    # Create server service
    & $NssmPath install AugmentoriumServer $ServerBatch
    & $NssmPath set AugmentoriumServer DisplayName "Augmentorium MCP Server"
    & $NssmPath set AugmentoriumServer Description "Augmentorium MCP server for LLM integration"
    & $NssmPath set AugmentoriumServer AppStdout "$LogsDir\server-output.log"
    & $NssmPath set AugmentoriumServer AppStderr "$LogsDir\server-error.log"
    & $NssmPath set AugmentoriumServer AppRotateFiles 1
    & $NssmPath set AugmentoriumServer AppRotateOnline 1
    & $NssmPath set AugmentoriumServer AppRotateSeconds 86400
    & $NssmPath set AugmentoriumServer Start SERVICE_AUTO_START
    
    # Start services
    Write-Host "Starting services..." -ForegroundColor Yellow
    Start-Service AugmentoriumIndexer
    Start-Service AugmentoriumServer
    
    Write-Host "Services installed and started!" -ForegroundColor Green
    Write-Host "You can manage them in the Windows Services control panel." -ForegroundColor Green
}
else {
    Write-Host "Not running as administrator. Creating startup scripts instead..." -ForegroundColor Yellow
    
    # Create startup scripts
    $StartupScript = @"
@echo off
start "" "$BinDir\augmentorium-indexer.bat"
start "" "$BinDir\augmentorium-server.bat"
"@
    
    Set-Content -Path "$BinDir\augmentorium-startup.bat" -Value $StartupScript
    
    # Create shortcut in Startup folder
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$StartupDir\Augmentorium.lnk")
    $Shortcut.TargetPath = "$BinDir\augmentorium-startup.bat"
    $Shortcut.WorkingDirectory = $BinDir
    $Shortcut.Description = "Start Augmentorium services"
    $Shortcut.Save()
    
    Write-Host "Startup shortcut created!" -ForegroundColor Green
    Write-Host "Augmentorium will start automatically when you log in." -ForegroundColor Green
    
    # Start processes for the current session
    Write-Host "Starting processes for current session..." -ForegroundColor Yellow
    Start-Process -FilePath $IndexerBatch -WindowStyle Minimized
    Start-Process -FilePath $ServerBatch -WindowStyle Minimized
}

# Create PowerShell profile with aliases if it doesn't exist
$ProfileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
}

if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

# Add aliases to PowerShell profile
Write-Host "Adding aliases to PowerShell profile..." -ForegroundColor Yellow
$ProfileContent = @"

# Augmentorium aliases
function Start-Augmentorium {
    if (Get-Service AugmentoriumIndexer -ErrorAction SilentlyContinue) {
        Start-Service AugmentoriumIndexer
        Start-Service AugmentoriumServer
        Write-Host "Augmentorium services started." -ForegroundColor Green
    } else {
        Start-Process -FilePath "$BinDir\augmentorium-indexer.bat" -WindowStyle Minimized
        Start-Process -FilePath "$BinDir\augmentorium-server.bat" -WindowStyle Minimized
        Write-Host "Augmentorium processes started." -ForegroundColor Green
    }
}

function Stop-Augmentorium {
    if (Get-Service AugmentoriumIndexer -ErrorAction SilentlyContinue) {
        Stop-Service AugmentoriumServer
        Stop-Service AugmentoriumIndexer
        Write-Host "Augmentorium services stopped." -ForegroundColor Green
    } else {
        Get-Process -Name "python" -ErrorAction SilentlyContinue | 
            Where-Object { `$_.CommandLine -like "*augmentorium*" } | 
            Stop-Process -Force
        Write-Host "Augmentorium processes stopped." -ForegroundColor Green
    }
}

function Get-AugmentoriumStatus {
    if (Get-Service AugmentoriumIndexer -ErrorAction SilentlyContinue) {
        Get-Service AugmentoriumIndexer, AugmentoriumServer | Format-Table -AutoSize
    } else {
        Get-Process -Name "python" -ErrorAction SilentlyContinue | 
            Where-Object { `$_.CommandLine -like "*augmentorium*" } | 
            Format-Table Id, ProcessName, StartTime -AutoSize
    }
}

function Get-AugmentoriumLogs {
    Get-Content -Path "$LogsDir\indexer-output.log", "$LogsDir\server-output.log" -Tail 20
}

function Watch-AugmentoriumLogs {
    Get-Content -Path "$LogsDir\indexer-output.log", "$LogsDir\server-output.log" -Tail 20 -Wait
}

function Set-AugmentoriumProject {
    param (
        [Parameter(Mandatory=`$true)]
        [string]`$ProjectPath
    )
    & "$VenvPath\Scripts\augmentorium-setup.exe" `$ProjectPath
}

Set-Alias -Name augmentorium-start -Value Start-Augmentorium
Set-Alias -Name augmentorium-stop -Value Stop-Augmentorium
Set-Alias -Name augmentorium-status -Value Get-AugmentoriumStatus
Set-Alias -Name augmentorium-logs -Value Get-AugmentoriumLogs
Set-Alias -Name augmentorium-watch -Value Watch-AugmentoriumLogs
Set-Alias -Name augmentorium-setup -Value Set-AugmentoriumProject
"@

Add-Content -Path $PROFILE -Value $ProfileContent

# Create setup helper script
$SetupHelperScript = @"
@echo off
call "$VenvPath\Scripts\activate.bat"
augmentorium-setup %*
"@

Set-Content -Path "$BinDir\augmentorium-setup.bat" -Value $SetupHelperScript

# Add bin directory to PATH for the current session
$env:PATH = "$BinDir;$env:PATH"

# Installation complete
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "     Augmentorium installation complete     " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services are running in the background."
Write-Host "You can manage them with the following PowerShell commands:"
Write-Host "  augmentorium-start  - Start services" -ForegroundColor Yellow
Write-Host "  augmentorium-stop   - Stop services" -ForegroundColor Yellow
Write-Host "  augmentorium-status - Check service status" -ForegroundColor Yellow
Write-Host "  augmentorium-logs   - View service logs" -ForegroundColor Yellow
Write-Host "  augmentorium-watch  - Watch logs in real-time" -ForegroundColor Yellow
Write-Host ""
Write-Host "To set up a new project, use:" 
Write-Host "  augmentorium-setup PATH_TO_PROJECT" -ForegroundColor Yellow
Write-Host ""
Write-Host "Please restart your PowerShell session to use these commands."
Write-Host ""
Write-Host "Enjoy using Augmentorium!" -ForegroundColor Green

# Deactivate virtual environment
deactivate
