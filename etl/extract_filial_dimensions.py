import os, sys, asyncio, json, time
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

QLIK_URL = "https://sense.farmaciassaojoao.com.br"
APP_ID = "671fa4f4-eb7d-418f-b4c9-936e87d8011d"
SHEET_ID = "ddd70c77-1a06-40d9-aff2-efa4b6b67b24"
SHEET_URL = f"{QLIK_URL}/sense/app/{APP_ID}/sheet/{SHEET_ID}/state/analysis"

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

async def main():
    async with async_playwright() as p:
        print("1. Conectando ao Qlik Sense...")
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD},
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(8000)
        
        print("2. Extraindo listas de Diretor, Distrital, Coordenador e Laboratório do Qlik...")
        result = await page.evaluate('''async () => {
            const wsUrl = `wss://${window.location.host}/app/${encodeURIComponent('671fa4f4-eb7d-418f-b4c9-936e87d8011d')}?reloadUri=https://${window.location.host}/`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                const results = {};
                let msgId = 1;
                const pending = {};
                
                function send(method, handle, params) {
                    return new Promise((res, rej) => {
                        const id = msgId++;
                        pending[id] = { res, rej };
                        ws.send(JSON.stringify({ "jsonrpc": "2.0", "id": id, "method": method, "handle": handle, "params": params }));
                    });
                }
                
                async function fetchDimValues(fieldName) {
                    const c = await send("CreateSessionObject", docHandle, [{
                        "qInfo": { "qType": "q_dim_" + fieldName },
                        "qHyperCubeDef": {
                            "qDimensions": [{ "qDef": { "qFieldDefs": [fieldName] } }],
                            "qMeasures": [{ "qDef": { "qDef": "Count(1)", "qLabel": "cnt" } }],
                            "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1500, "qWidth": 2 }],
                            "qSuppressZero": true, "qSuppressMissing": true
                        }
                    }]);
                    const h = c.result.qReturn.qHandle;
                    const l = await send("GetLayout", h, []);
                    return (l.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix || [])
                        .map(r => r[0].qText)
                        .filter(x => x && x !== '-' && x !== 'null');
                }
                
                ws.onopen = async () => {
                    try {
                        const openRes = await send("OpenDoc", -1, ["671fa4f4-eb7d-418f-b4c9-936e87d8011d"]);
                        docHandle = openRes.result.qReturn.qHandle;
                        
                        results.diretores = await fetchDimValues("Diretor");
                        results.distritais = await fetchDimValues("Distrital");
                        results.coordenadores = await fetchDimValues("Coordenador");
                        results.laboratorios = await fetchDimValues("Laboratorio");
                        
                        resolve(results);
                        ws.close();
                    } catch (e) {
                        resolve({ error: e.message });
                    }
                };
                
                ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    if (msg.id && pending[msg.id]) {
                        if (msg.error) pending[msg.id].rej(new Error(msg.error.message));
                        else pending[msg.id].res(msg);
                        delete pending[msg.id];
                    }
                };
            });
        }''')
        
        print("\n📋 DIRETORES ENCONTRADOS NO QLIK:", result.get('diretores', []))
        print("📋 QTD DISTRITAIS:", len(result.get('distritais', [])))
        print("📋 QTD COORDENADORES:", len(result.get('coordenadores', [])))
        print("📋 QTD LABORATÓRIOS:", len(result.get('laboratorios', [])))
        
        # Salvar no filtro_hierarquia de agosto
        p_filtros = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'agosto', 'filtro_hierarquia.json')
        if os.path.exists(p_filtros):
            with open(p_filtros, 'r', encoding='utf-8') as f:
                cur_fh = json.load(f)
            cur_fh['diretores'] = sorted(result.get('diretores', []))
            cur_fh['distritais'] = sorted(result.get('distritais', []))
            cur_fh['coordenadores'] = sorted(result.get('coordenadores', []))
            cur_fh['laboratorios'] = sorted(result.get('laboratorios', []))
            with open(p_filtros, 'w', encoding='utf-8') as f:
                json.dump(cur_fh, f, ensure_ascii=False, indent=2)
            print(f"✅ Arquivo {p_filtros} atualizado com as dimensões reais do Qlik Sense!")
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
