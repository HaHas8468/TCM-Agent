$ErrorActionPreference = 'Stop'

Set-Location -LiteralPath $PSScriptRoot

$viteEntry = Join-Path $PSScriptRoot 'node_modules\vite\bin\vite.js'
$bundledNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'

if (-not (Test-Path -LiteralPath $viteEntry)) {
  Write-Host 'Vite entry file was not found. Please make sure project dependencies are available.' -ForegroundColor Red
  exit 1
}

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$nodeExecutable = $null

if ($nodeCommand) {
  $nodeExecutable = $nodeCommand.Source
} elseif (Test-Path -LiteralPath $bundledNode) {
  $nodeExecutable = $bundledNode
}

if (-not $nodeExecutable) {
  Write-Host 'No usable Node.js was detected. Please install Node.js, or ask me to start the preview for you.' -ForegroundColor Red
  exit 1
}

& $nodeExecutable $viteEntry build
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

& $nodeExecutable $viteEntry preview --host 127.0.0.1 --port 4173
exit $LASTEXITCODE
