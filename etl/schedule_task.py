import sys, os, subprocess

python_exe = sys.executable
script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'etl', 'sync_qlik.py')
cmd_task = f'"{python_exe}" "{script_path}"'

cmd = [
    'schtasks', '/create',
    '/tn', 'Sincronizador_Qlik_Dashboard',
    '/tr', cmd_task,
    '/sc', 'daily',
    '/st', '07:30',
    '/f'
]

print("Executando:", ' '.join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Returncode:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)

