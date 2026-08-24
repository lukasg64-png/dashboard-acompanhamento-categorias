import sys, os, subprocess, base64

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_exe = sys.executable
script_abs = os.path.join(BASE_DIR, "etl", "daily_refresh.py")

ps_script = f"""
$Action = New-ScheduledTaskAction -Execute "{python_exe}" -Argument '"{script_abs}"' -WorkingDirectory "{BASE_DIR}"
$Trigger = New-ScheduledTaskTrigger -Daily -At 07:30
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 10) -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName "Sincronizador_Qlik_Dashboard" -Action $Action -Trigger $Trigger -Settings $Settings -Force
"""

print(f"Registrando tarefa agendada no Windows para: {script_abs}")
encoded_cmd = base64.b64encode(ps_script.encode('utf-16le')).decode('ascii')
res = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded_cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')

print("Returncode:", res.returncode)
if res.stdout.strip():
    print("Stdout:", res.stdout.strip())
if res.stderr.strip():
    print("Stderr:", res.stderr.strip())
if res.returncode == 0:
    print("✅ Tarefa 'Sincronizador_Qlik_Dashboard' agendada com sucesso para 07:30 (com suporte a UTF-8, StartWhenAvailable, bateria e retentativas automáticas)!")

