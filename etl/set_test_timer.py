import sys, os, subprocess, base64
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_exe = sys.executable
script_abs = os.path.join(BASE_DIR, "etl", "daily_refresh.py")

# Adicionar 3 minutos
target_time = datetime.now() + timedelta(minutes=3)
time_str = target_time.strftime("%H:%M")

ps_script = f"""
$Action = New-ScheduledTaskAction -Execute "{python_exe}" -Argument '"{script_abs}"' -WorkingDirectory "{BASE_DIR}"
$Trigger = New-ScheduledTaskTrigger -Once -At "{time_str}"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 10) -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName "Sincronizador_Qlik_Dashboard" -Action $Action -Trigger $Trigger -Settings $Settings -Force
"""

print(f"⏱️ Agendando tarefa de teste para as: {time_str} (daqui a ~3 minutos)...")
encoded_cmd = base64.b64encode(ps_script.encode('utf-16le')).decode('ascii')
res = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded_cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')

if res.returncode == 0:
    print(f"✅ Tarefa 'Sincronizador_Qlik_Dashboard' agendada com sucesso para disparar às {time_str}!")
else:
    print("❌ Erro ao agendar:", res.stderr)
