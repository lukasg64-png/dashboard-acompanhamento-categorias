import asyncio, ssl, json
import websockets

async def test_qlik():
    app_id = '671fa4f4-eb7d-418f-b4c9-936e87d8011d'
    ws_url = f'wss://sense.farmaciassaojoao.com.br/app/{app_id}'

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    print(f"Tentando conexão WebSocket com Qlik App: {app_id}...")
    try:
        async with websockets.connect(ws_url, ssl=ssl_ctx) as ws:
            print("Connected! Sending OpenDoc...")
            req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "OpenDoc",
                "handle": -1,
                "params": [app_id]
            }
            await ws.send(json.dumps(req))
            msg = await ws.recv()
            print("Response:", msg[:300])
    except Exception as e:
        print("WebSocket Error:", e)

if __name__ == '__main__':
    asyncio.run(test_qlik())
