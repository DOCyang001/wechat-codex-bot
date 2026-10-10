param([switch]$SkipProfiles)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
Set-Location -LiteralPath $taskRoot
function Run-Checked([string]$Executable,[string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {throw "命令执行失败：$Executable"}
}
foreach ($required in @('git','node','npm')) {
    if (!(Get-Command $required -ErrorAction SilentlyContinue)) {throw "请先安装 $required，并重新打开终端。"}
}
$env:PYTHONIOENCODING='utf-8'
$env:NO_PROXY='localhost,127.0.0.1,::1'
# Use the same simple Windows system-proxy form supported by the model bridge.
$proxy=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
if ($proxy.ProxyEnable -and $proxy.ProxyServer -and $proxy.ProxyServer -notmatch '=') {
    if (!$env:HTTPS_PROXY) {$env:HTTPS_PROXY="http://$($proxy.ProxyServer)"}
    if (!$env:HTTP_PROXY) {$env:HTTP_PROXY="http://$($proxy.ProxyServer)"}
}
$taskPython=Join-Path $taskRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $taskPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        Run-Checked 'py' @('-3.11','-m','venv','.venv')
    } else {
        Run-Checked 'python' @('-c','import sys; assert sys.version_info[:2] == (3,11), "Python 3.11 required"')
        Run-Checked 'python' @('-m','venv','.venv')
    }
}
Run-Checked $taskPython @('-m','pip','install','-r','requirements.txt')
Run-Checked $taskPython @('-m','pip','check')
$npmRoot=(& npm.cmd root -g | Select-Object -Last 1).Trim()
if ($LASTEXITCODE -ne 0) {throw '无法确定 npm 全局安装目录。'}
$cli=Join-Path $npmRoot '@openai\codex\bin\codex.js'
if (!(Test-Path -LiteralPath $cli)) {
    Run-Checked 'npm.cmd' @('install','-g','@openai/codex@0.159.2')
}
if (!(Test-Path -LiteralPath $cli)) {throw 'Codex CLI 安装失败。'}
Run-Checked 'node' @($cli,'--version')
& node $cli login status
if ($LASTEXITCODE -ne 0) {
    Write-Host '请在浏览器中使用自己的 ChatGPT 账号登录 Codex。'
    Run-Checked 'node' @($cli,'login')
}
Run-Checked $taskPython @('configure.py','--codex-cli-js',$cli)
Run-Checked $taskPython @('setup_bot.py')
if (!$SkipProfiles) {
    Write-Host '请保持微信已登录。接下来只读取指定聊天并生成语气档案，不发送消息。'
    Run-Checked $taskPython @('prepare_profiles.py')
}
Write-Host '安装完成。运行 start.cmd 才会启用自动回复；停止请运行 stop.cmd。'
