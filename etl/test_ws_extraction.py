import os, sys, asyncio, json
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright
import websockets, ssl

QLIK_URL = "https://sense.farmaciassaojoao.com.br"
APP_ID = "671fa4f4-eb7d-418f-b4c9-936e87d8011d"
SHEET_ID = "ddd70c77-1a06-40d9-aff2-efa4b6b67b24"
SHEET_URL = f"{QLIK_URL}/sense/app/{APP_ID}/sheet/{SHEET_ID}/state/analysis"

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

async def get_session():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD}
        )
        page = await context.new_page()
        print("1. Obtendo sessão NTLM no Qlik Sense...")
        await page.goto(SHEET_URL, timeout=45000)
        await page.wait_for_timeout(6000)
        
        cookies = await context.cookies()
        session_cookie = None
        all_cookies = []
        for c in cookies:
            all_cookies.append(f"{c['name']}={c['value']}")
            if c['name'] == 'X-Qlik-Session':
                session_cookie = c['value']
                
        cookie_header = "; ".join(all_cookies)
        print(f"✅ Sessão capturada! X-Qlik-Session: {session_cookie}")
        await browser.close()
        return cookie_header

async def extract_table(cookie_header):
    print("\n2. Conectando à Engine API via WebSocket nativo...")
    ws_url = f"wss://sense.farmaciassaojoao.com.br/app/{APP_ID}"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = [
        ("Cookie", cookie_header),
        ("User-Agent", "Mozilla/5.0")
    ]
    
    # Suporte a websockets v13/v14
    try:
        ws_conn = websockets.connect(ws_url, ssl=ssl_context, additional_headers=headers)
    except TypeError:
        ws_conn = websockets.connect(ws_url, ssl=ssl_context, extra_headers=headers)
        
    async with ws_conn as ws:
        print("✅ WebSocket conectado!")
        
        # 1. OpenDoc
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "OpenDoc",
            "handle": -1,
            "params": [APP_ID]
        }))
        
        doc_handle = None
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1 and msg.get('result'):
                doc_handle = msg['result']['qReturn']['qHandle']
                print(f"✅ App aberto com sucesso! Handle: {doc_handle}")
                break
            elif msg.get('id') == 1 and msg.get('error'):
                print(f"❌ Erro no OpenDoc: {msg['error']}")
                return
                
        # 2. GetObject ZKJqXsu
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "GetObject",
            "handle": doc_handle,
            "params": ["ZKJqXsu"]
        }))
        
        obj_handle = None
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 2 and msg.get('result'):
                obj_handle = msg['result']['qReturn']['qHandle']
                print(f"✅ Objeto ZKJqXsu obtido! Handle: {obj_handle}")
                break
                
        # 3. GetLayout
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "GetLayout",
            "handle": obj_handle,
            "params": []
        }))
        
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 3 and msg.get('result'):
                layout = msg['result']['qLayout']
                title = layout.get('title') or layout.get('qMeta', {}).get('title')
                hc = layout.get('qHyperCube', {})
                dims = [d.get('qFallbackTitle', '') for d in hc.get('qDimensionInfo', [])]
                meas = [m.get('qFallbackTitle', '') for m in hc.get('qMeasureInfo', [])]
                print(f"✅ Layout obtido! Título: {title}")
                print(f"   Dimensões ({len(dims)}): {dims}")
                print(f"   Métricas ({len(meas)}): {meas}")
                print(f"   Tamanho estimado qSize: {hc.get('qSize')}")
                break

async def main():
    cookie_header = await get_session()
    await extract_table(cookie_header)

if __name__ == '__main__':
    asyncio.run(main())
