param(
    [ValidateSet('start', 'stop', 'status', 'logs', 'build')]
    [string]$Action = 'status'
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    switch ($Action) {
        'start' { & docker compose up -d --no-build }
        'stop' { & docker compose stop }
        'status' { & docker compose ps }
        'logs' { & docker compose logs --tail=80 api worker }
        'build' { & docker compose build api web sandbox-provisioner minio }
    }
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed: $LASTEXITCODE" }
} finally {
    Pop-Location
}
