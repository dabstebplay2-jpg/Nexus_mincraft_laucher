param(
    [string]$Python = "python",
    [string]$ISCCPath = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

powershell -ExecutionPolicy Bypass -File ".\scripts\build_release.ps1" -Python $Python
if ($LASTEXITCODE -ne 0) {
    throw "build_release.ps1 failed with code $LASTEXITCODE"
}

if ($ISCCPath) {
    powershell -ExecutionPolicy Bypass -File ".\scripts\build_installer.ps1" -Python $Python -SkipReleaseBuild -ISCCPath $ISCCPath
} else {
    powershell -ExecutionPolicy Bypass -File ".\scripts\build_installer.ps1" -Python $Python -SkipReleaseBuild
}

if ($LASTEXITCODE -ne 0) {
    throw "build_installer.ps1 failed with code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Full release ready in .\release" -ForegroundColor Green
Get-ChildItem .\release
