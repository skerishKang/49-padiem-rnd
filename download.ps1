##############################################################################
# Blackbox CLI v2 Install Script for Windows PowerShell (Extension Service Version)
#
# This script downloads and installs the Blackbox CLI v2 (Node.js-based)
# from the Extension Upload Service.
#
# Usage:
#   Invoke-WebRequest -Uri "https://releases.blackbox.ai/api/scripts/blackbox-cli-v2/download.ps1" -OutFile "download.ps1"; .\download.ps1
##############################################################################

$ErrorActionPreference = "Stop"

# --- 1) Check for Node.js and npm ---
Write-Host "Checking for Node.js..." -ForegroundColor Gray
try {
    $nodeVersion = node --version
    $nodeMajorVersion = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($nodeMajorVersion -lt 20) {
        Write-Error "Node.js version 20 or higher is required. Current version: $nodeVersion"
        Write-Host "Please upgrade Node.js from https://nodejs.org/ and try again." -ForegroundColor Red
        exit 1
    }
    Write-Host "Found Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js is not installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "To install Node.js:" -ForegroundColor Yellow
    Write-Host "1. Visit https://nodejs.org/" -ForegroundColor Yellow
    Write-Host "2. Download the LTS version for Windows" -ForegroundColor Yellow
    Write-Host "3. Run the installer and follow the prompts" -ForegroundColor Yellow
    Write-Host "4. Restart your terminal and run this script again" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or use a package manager:" -ForegroundColor Yellow
    Write-Host "  winget install OpenJS.NodeJS.LTS" -ForegroundColor Cyan
    Write-Host "  choco install nodejs-lts" -ForegroundColor Cyan
    exit 1
}

# Check for npm
try {
    $npmVersion = npm --version
    Write-Host "Found npm $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "npm is not installed or not in PATH." -ForegroundColor Red
    Write-Host "npm should be installed with Node.js. Please reinstall Node.js from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# --- 2) Variables ---
$PRODUCT_SLUG = "blackbox-cli-v2"
$EXTENSION_SERVICE_URL = if ($env:EXTENSION_SERVICE_URL) { $env:EXTENSION_SERVICE_URL } else { "https://releases.blackbox.ai" }

if (-not $env:BLACKBOX_INSTALL_DIR) {
    $env:BLACKBOX_INSTALL_DIR = Join-Path $env:USERPROFILE ".blackbox-cli-v2"
}
if (-not $env:BLACKBOX_BIN_DIR) {
    $env:BLACKBOX_BIN_DIR = Join-Path $env:USERPROFILE ".local\bin"
}

$CONFIGURE = if ($env:CONFIGURE -eq "false") { "false" } else { "true" }

# --- 3) Detect Architecture ---
$ARCH = $env:PROCESSOR_ARCHITECTURE
if ($ARCH -eq "AMD64") {
    $PLATFORM = "win-x64"
} elseif ($ARCH -eq "ARM64") {
    Write-Error "Windows ARM64 is not currently supported."
    exit 1
} else {
    Write-Error "Unsupported architecture '$ARCH'. Only x86_64 is supported on Windows."
    exit 1
}

# --- 4) Get latest release information ---
Write-Host "Fetching latest release information for platform: $PLATFORM..." -ForegroundColor Gray

$RELEASE_API_URL = "$EXTENSION_SERVICE_URL/api/v0/latest?product=$PRODUCT_SLUG&platform=$PLATFORM"

try {
    $RELEASE_INFO = Invoke-WebRequest -Uri $RELEASE_API_URL -UseBasicParsing | ConvertFrom-Json
    Write-Host "Successfully fetched release information." -ForegroundColor Green
} catch {
    Write-Error "Failed to fetch release information from $RELEASE_API_URL. Error: $($_.Exception.Message)"
    Write-Host "Please check that the extension service is available and the product '$PRODUCT_SLUG' exists." -ForegroundColor Red
    exit 1
}

# Extract download URL and version
$DOWNLOAD_URL = $RELEASE_INFO.url
$VERSION = $RELEASE_INFO.version

if (-not $DOWNLOAD_URL) {
    Write-Error "Could not parse download URL from release information"
    Write-Host "Release info: $($RELEASE_INFO | ConvertTo-Json)" -ForegroundColor Red
    exit 1
}

if (-not $DOWNLOAD_URL.StartsWith("http")) {
    $DOWNLOAD_URL = "$EXTENSION_SERVICE_URL$DOWNLOAD_URL"
}

Write-Host "Downloading Blackbox CLI v2 version $VERSION from: $DOWNLOAD_URL" -ForegroundColor Blue

# --- 5) Download the file ---
$FILENAME = Split-Path $DOWNLOAD_URL -Leaf
if (-not $FILENAME -or $FILENAME -eq "") {
    $FILENAME = "blackbox-cli-v2-$PLATFORM.zip"
}

try {
    Invoke-WebRequest -Uri $DOWNLOAD_URL -OutFile $FILENAME -UseBasicParsing
    Write-Host "Download completed successfully." -ForegroundColor Green
} catch {
    Write-Error "Failed to download $DOWNLOAD_URL. Error: $($_.Exception.Message)"
    exit 1
}

# --- 6) Remove existing installation if present ---
if (Test-Path $env:BLACKBOX_INSTALL_DIR) {
    Write-Host "Removing existing installation at $env:BLACKBOX_INSTALL_DIR..." -ForegroundColor DarkYellow
    Remove-Item -Path $env:BLACKBOX_INSTALL_DIR -Recurse -Force
}

if (Test-Path $env:BLACKBOX_BIN_DIR) {
    Write-Host "Removing old blackbox executables from $env:BLACKBOX_BIN_DIR..." -ForegroundColor DarkYellow
    Remove-Item -Path (Join-Path $env:BLACKBOX_BIN_DIR "blackbox.cmd") -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $env:BLACKBOX_BIN_DIR "blackbox.mjs") -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $env:BLACKBOX_BIN_DIR "blackbox") -Force -ErrorAction SilentlyContinue
}

# --- 7) Create installation directory and extract ---
Write-Host "Creating installation directory: $env:BLACKBOX_INSTALL_DIR" -ForegroundColor DarkYellow
New-Item -ItemType Directory -Path $env:BLACKBOX_INSTALL_DIR -Force | Out-Null

Write-Host "Extracting $FILENAME..." -ForegroundColor Gray
try {
    Expand-Archive -Path $FILENAME -DestinationPath $env:BLACKBOX_INSTALL_DIR -Force
    Write-Host "Extraction completed successfully." -ForegroundColor Green
} catch {
    Write-Error "Failed to extract $FILENAME. Error: $($_.Exception.Message)"
    Remove-Item -Path $FILENAME -Force -ErrorAction SilentlyContinue
    exit 1
}

Remove-Item -Path $FILENAME -Force

# --- 8) Install npm package globally
npm i -g @blackbox_ai/blackbox-cli

blackbox --version

Write-Host "Installation completed successfully. You can now use the 'blackbox' command (after updating PATH or restarting terminal)" -ForegroundColor Green

exit 0
