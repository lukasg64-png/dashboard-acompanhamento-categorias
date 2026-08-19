const http = require('http');
const fs = require('fs');
const path = require('path');
const localtunnel = require('localtunnel');

const PORT = 8085;
const DIST_FILE = path.join(__dirname, 'dist', 'index.html');

const server = http.createServer((req, res) => {
  if (fs.existsSync(DIST_FILE)) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    fs.createReadStream(DIST_FILE).pipe(res);
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('dist/index.html não encontrado. Execute python etl/update_dashboard.py primeiro.');
  }
});

server.listen(PORT, async () => {
  console.log(`Servidor local rodando em http://localhost:${PORT}`);
  try {
    const tunnel = await localtunnel({ port: PORT });
    console.log('🌐 LINK PÚBLICO (localtunnel): ' + tunnel.url);

    tunnel.on('close', () => console.log('Tunnel fechado'));
    tunnel.on('error', (err) => console.error('Erro no tunnel:', err));
  } catch (err) {
    console.error('Erro ao iniciar tunnel:', err);
  }
});

