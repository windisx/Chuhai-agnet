# 仅首次复制使用。目标状态目录存在时拒绝执行，防止覆盖新项目数据。
$ErrorActionPreference = 'Stop'
$sourceRoot = 'E:\Agent_project\Yuxi-main\Yuxi-main'
$targetRoot = 'E:\Agent_project\Yuxi-main\ChuHai-agent'
$sourceState = Join-Path $sourceRoot 'docker\volumes'
$targetState = Join-Path $targetRoot 'docker\volumes'
if (Test-Path -LiteralPath $targetState) { throw 'Target state directory already exists. Refusing to overwrite.' }
Push-Location $sourceRoot
try {
    & docker compose stop --timeout 60
    if ($LASTEXITCODE -ne 0) { throw 'Failed to cleanly stop original services.' }
    New-Item -ItemType Directory -Path $targetState -Force | Out-Null
    & robocopy $sourceState $targetState /E /XJ /COPY:DAT /DCOPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) { throw "State copy failed: $LASTEXITCODE" }
    & python (Join-Path $targetRoot 'deployment\复制校验数据.py')
    if ($LASTEXITCODE -ne 0) { throw 'State byte verification failed.' }
} finally {
    # 即使复制失败也恢复原服务；绝不执行 down -v 或删除原数据。
    & docker compose up -d --no-build
    $restoreResult = $LASTEXITCODE
    Pop-Location
    if ($restoreResult -ne 0) { throw 'Original services need recovery: docker compose up -d --no-build' }
}
