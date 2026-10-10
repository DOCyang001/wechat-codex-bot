$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
$taskRuntime = Join-Path $taskRoot 'runtime'
New-Item -ItemType Directory -Force -Path $taskRuntime | Out-Null
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$(Join-Path $taskRoot '.venv\Scripts');$env:PATH"
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
if (!(Test-Path -LiteralPath (Join-Path $taskRuntime 'setup_report.json'))) {
    throw '聊天语气档案尚未完成，暂不启用自动回复。'
}
foreach ($service in @(@{Name='bridge';File='codex_bridge.py';Port=8766}, @{Name='ui';File='bot_ui.py';Port=8765})) {
    $healthPath = if ($service.Name -eq 'bridge') {'/health'} else {'/local_instance'}
    $existingService=$null
    try {
        $existingService = Invoke-RestMethod -Uri "http://127.0.0.1:$($service.Port)$healthPath" -TimeoutSec 2
    } catch {}
    if ($existingService) {
        if ($existingService.instance -ne $taskRoot) {throw "端口 $($service.Port) 已被另一份服务占用，请先停止它。"}
        continue
    }
    if (Get-NetTCPConnection -State Listen -LocalPort $service.Port -ErrorAction SilentlyContinue) {
        throw "端口 $($service.Port) 已被占用，未结束任何其他进程。"
    }
    $serviceScript = Join-Path $taskRoot $service.File
    $taskProcess = Start-Process -FilePath $taskPython -ArgumentList @('-u', "`"$serviceScript`"") -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRuntime "$($service.Name).out.log") -RedirectStandardError (Join-Path $taskRuntime "$($service.Name).err.log")
    @{pid=$taskProcess.Id;created=$taskProcess.StartTime.ToUniversalTime().ToString('o');script=$serviceScript} | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath (Join-Path $taskRuntime "$($service.Name).pid.json")
}
for ($attempt=0; $attempt -lt 20; $attempt++) {
    try {
        $null=Invoke-RestMethod 'http://127.0.0.1:8765/bot_status' -TimeoutSec 2
        $null=Invoke-RestMethod 'http://127.0.0.1:8766/health' -TimeoutSec 2
        break
    } catch { Start-Sleep -Milliseconds 500 }
}
$state=Invoke-RestMethod -Method Post 'http://127.0.0.1:8765/start_bot' -TimeoutSec 10
for ($attempt=0; $attempt -lt 40; $attempt++) {
    try {
        $ready=Invoke-RestMethod 'http://127.0.0.1:8765/local_status' -TimeoutSec 2
        Write-Output '机器人监听已就绪。控制面板：http://127.0.0.1:8765/'
        exit 0
    } catch {Start-Sleep -Milliseconds 500}
}
throw '启动请求已提交，但监听尚未就绪。请查看 runtime 日志或控制面板。'

