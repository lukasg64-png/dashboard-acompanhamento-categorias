import sys, os, subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_exe = sys.executable
script_rel = "etl/daily_refresh.py"

ps_cmd = f"""
$Action = New-ScheduledTaskAction -Execute "{python_exe}" -Argument "{script_rel}" -WorkingDirectory "{BASE_DIR}"
$Trigger = New-ScheduledTaskTrigger -Daily -At 07:30
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName "Sincronizador_Qlik_Dashboard" -Action $Action -Trigger $Trigger -Settings $Settings -Force
"""

print("Registrando tarefa agendada no Windows...")
res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
print("Returncode:", res.returncode)
if res.stdout.strip():
    print("Stdout:", res.stdout.strip())
if res.stderr.strip():
    print("Stderr:", res.stderr.strip())
if res.returncode == 0:
    print("✅ Tarefa 'Sincronizador_Qlik_Dashboard' agendada com sucesso para 07:30 (com StartWhenAvailable e suporte a bateria)!")

