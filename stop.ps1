$ErrorActionPreference='Stop'
try {
    $instance=Invoke-RestMethod 'http://127.0.0.1:8765/local_instance' -TimeoutSec 2
    if ($instance.instance -eq $PSScriptRoot) {
        $null=Invoke-RestMethod -Method Post 'http://127.0.0.1:8765/stop_bot' -TimeoutSec 15
    }
} catch {}
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'stop_services.py')
Write-Output '机器人已停止。'
