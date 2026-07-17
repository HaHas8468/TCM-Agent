$ErrorActionPreference = 'Stop'

Set-Location -LiteralPath $PSScriptRoot

$viteEntry = Join-Path $PSScriptRoot 'node_modules\vite\bin\vite.js'
$bundledNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'

if (-not (Test-Path -LiteralPath $viteEntry)) {
  Write-Host 'Vite entry file was not found. Please make sure project dependencies are available.' -ForegroundColor Red
  exit 1
}

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue

if ($nodeCommand) {
  & $nodeCommand.Source $viteEntry --host 127.0.0.1 --port 5173
  exit $LASTEXITCODE
}

if (Test-Path -LiteralPath $bundledNode) {
  & $bundledNode $viteEntry --host 127.0.0.1 --port 5173
  exit $LASTEXITCODE
}

Write-Host 'No usable Node.js was detected. Please install Node.js, or ask me to start the preview for you.' -ForegroundColor Red
exit 1
