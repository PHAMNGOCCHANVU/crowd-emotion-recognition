$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $repoRoot 'backend/.venv/Scripts/python.exe'

if (-not (Test-Path -LiteralPath $backendPython)) {
    throw 'Missing backend/.venv. Create it and install backend/requirements.txt first; see README.md.'
}

Push-Location -LiteralPath $repoRoot
try {
    & $backendPython -c 'import uvicorn, bcrypt'
    if ($LASTEXITCODE -ne 0) {
        throw 'Backend dependencies are missing. Run: .\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt'
    }
    & $backendPython -X utf8 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
    if ($LASTEXITCODE -ne 0) {
        throw 'Backend failed to start. Read the error above; verify that port 8000 is available.'
    }
}
finally {
    Pop-Location
}
