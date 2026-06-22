[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('up', 'smoke', 'data', 'down', 'clean')]
    [string]$Action
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$compose = Join-Path $repoRoot 'docker/docker-compose.yml'

switch ($Action) {
    'up' {
        & docker compose -f $compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'Jupyter -> http://localhost:8888 (token: lakehouse)'
            Write-Host 'MinIO   -> http://localhost:9001 (minioadmin / minioadmin)'
        }
    }
    'smoke' { & docker compose -f $compose exec -T --user 1000:100 spark bash -lc 'export SPARK_HOME=/usr/local/spark; source /usr/local/bin/before-notebook.d/10spark-config.sh; python /workspace/scripts/verify.py' }
    'data'  { & docker compose -f $compose exec -T --user 1000:100 spark bash -lc 'export SPARK_HOME=/usr/local/spark; source /usr/local/bin/before-notebook.d/10spark-config.sh; python /workspace/scripts/generate_data.py' }
    'down'  { & docker compose -f $compose down }
    'clean' { & docker compose -f $compose down -v }
}

exit $LASTEXITCODE
