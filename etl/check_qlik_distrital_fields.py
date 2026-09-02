import asyncio, json, ssl, websockets

QLIK_WS_URL = "wss://sense.farmaciassaojoao.com.br/anon/app/462d7a22-cc4b-4c28-98e3-05bf8cb4a8f9"

async def check_qlik_fields():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    async with websockets.connect(QLIK_WS_URL, ssl=ctx, max_size=50*1024*1024) as ws:
        # OpenDoc
        await ws.send(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "OpenDoc",
            "handle": -1, "params": ["462d7a22-cc4b-4c28-98e3-05bf8cb4a8f9"]
        }))
        res = json.loads(await ws.recv())
        doc_handle = res.get('result', {}).get('qReturn', {}).get('qHandle', 1)
        print(f"Doc opened. Handle: {doc_handle}")

        # Test cube with Diretor, Distrital, Grupo, Linha
        # Receita Líquida Setembro 2026 Dia <= 1
        cube_def = {
            "jsonrpc": "2.0", "id": 2, "method": "CreateSessionObject",
            "handle": doc_handle,
            "params": [{
                "qInfo": {"qType": "DistritalLinhaCube"},
                "qHyperCubeDef": {
                    "qDimensions": [
                        {"qDef": {"qFieldDefs": ["Diretor Regional"]}},
                        {"qDef": {"qFieldDefs": ["Distrital"]}},
                        {"qDef": {"qFieldDefs": ["Grupo"]}},
                        {"qDef": {"qFieldDefs": ["Linha"]}}
                    ],
                    "qMeasures": [
                        {
                            "qDef": {
                                "qDef": "Sum({1<[Ano-Mes]={'2026-09'}, [Dia]={'<=1'}>} [Receita Líquida])",
                                "qLabel": "Venda_Set_26_D1"
                            }
                        },
                        {
                            "qDef": {
                                "qDef": "Sum({1<[Ano-Mes]={'2026-08'}>} [Receita Líquida])",
                                "qLabel": "Venda_Ago_26_Total"
                            }
                        },
                        {
                            "qDef": {
                                "qDef": "Sum({1<[Ano-Mes]={'2026-08'}, [Dia]={'<=1'}>} [Receita Líquida])",
                                "qLabel": "Venda_Ago_26_D1"
                            }
                        }
                    ],
                    "qInitialDataFetch": [{"qTop": 0, "qLeft": 0, "qHeight": 20, "qWidth": 7}]
                }
            }]
        }
        await ws.send(json.dumps(cube_def))
        res2 = json.loads(await ws.recv())
        obj_handle = res2.get('result', {}).get('qReturn', {}).get('qHandle')
        print(f"Session object handle: {obj_handle}")

        # GetLayout
        await ws.send(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "GetLayout", "handle": obj_handle, "params": []}))
        res3 = json.loads(await ws.recv())
        hc = res3.get('result', {}).get('qLayout', {}).get('qHyperCube', {})
        q_matrix = hc.get('qDataPages', [{}])[0].get('qMatrix', [])
        q_size = hc.get('qSize', {})
        print(f"HyperCube size: {q_size}")
        print(f"Sample rows ({len(q_matrix)}):")
        for row in q_matrix[:5]:
            vals = [col.get('qText') for col in row]
            print("  ", vals)

asyncio.run(check_qlik_fields())
