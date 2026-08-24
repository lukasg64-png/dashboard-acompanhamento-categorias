# Script PowerShell para registrar tarefa agendada do Qlik Dashboard
$ErrorActionPreference = "Stop"

# Obter diretório raiz real
$PSScriptRoot_Real = Split-Path -Parent $PSScriptRoot
if (-not $PSScriptRoot_Real) {
    $PSScriptRoot_Real = (Get-Item -LiteralPath ".").FullName
}

$PyExe = (Get-Command python.exe).Source
if (-not $PyExe) {
    $PyExe = "C:\Users\lucas.alves6\AppData\Local\Programs\Python\Python311\python.exe"
}

$ScriptPath = Join-Path $PSScriptRoot_Real "etl\daily_refresh.py"

Write-Host "Configurando Tarefa Agendada no Windows..."
Write-Host "  Diretório Base: $PSScriptRoot_Real"
Write-Host "  Python: $PyExe"
Write-Host "  Script: $ScriptPath"

$Action = New-ScheduledTaskAction -Execute $PyExe -Argument "`"$ScriptPath`"" -WorkingDirectory $PSScriptRoot_Real
$Trigger = New-ScheduledTaskTrigger -Daily -At 07:30
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 10) -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName "Sincronizador_Qlik_Dashboard" -Action $Action -Trigger $Trigger -Settings $Settings -Force

Write-Host "✅ Tarefa 'Sincronizador_Qlik_Dashboard' registrada com sucesso!"
