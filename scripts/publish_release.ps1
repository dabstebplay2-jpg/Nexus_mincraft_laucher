param(
    [string]$Version = "",
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"

cd (Split-Path -Parent $PSScriptRoot)

if (-not $Version) {
    $Version = "0.6.0"

    if (Test-Path ".\core\constants.py") {
        $constants = Get-Content ".\core\constants.py" -Raw
        if ($constants -match 'APP_VERSION\s*=\s*["'']([^"'']+)["'']') {
            $Version = $Matches[1]
        }
    }
}

$tag = "v$Version"
$releaseDir = "release"
$zipName = "NexusLauncher_Windows_$Version.zip"
$zipPath = Join-Path $releaseDir $zipName

New-Item -ItemType Directory -Force $releaseDir | Out-Null

if (-not $NoBuild) {
    Write-Host "Building Nexus Launcher..." -ForegroundColor Cyan

    if (-not (Test-Path ".\Nexus Launcher.spec")) {
        throw "Nexus Launcher.spec not found."
    }

    .\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm ".\Nexus Launcher.spec"
}

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

if (Test-Path ".\dist\Nexus Launcher") {
    Compress-Archive -Path ".\dist\Nexus Launcher\*" -DestinationPath $zipPath -Force
}
elseif (Test-Path ".\dist") {
    Compress-Archive -Path ".\dist\*" -DestinationPath $zipPath -Force
}
else {
    throw "dist folder not found. Build failed or PyInstaller output is missing."
}

Write-Host "Package created: $zipPath" -ForegroundColor Green

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "GitHub CLI not found." -ForegroundColor Yellow
    Write-Host "Upload this file manually to GitHub Releases:" -ForegroundColor Yellow
    Write-Host $zipPath -ForegroundColor Cyan
    exit 0
}

Write-Host "Creating GitHub release $tag..." -ForegroundColor Cyan

$existing = gh release view $tag 2>$null

if ($LASTEXITCODE -eq 0) {
    gh release upload $tag $zipPath --clobber
}
else {
    gh release create $tag $zipPath `
        --title "Nexus Launcher $Version" `
        --notes "Nexus Launcher release $Version" `
        --latest
}

Write-Host "Release published:" -ForegroundColor Green
Write-Host "https://github.com/dabstebplay2-jpg/Nexus_mincraft_laucher/releases/latest" -ForegroundColor Cyan
