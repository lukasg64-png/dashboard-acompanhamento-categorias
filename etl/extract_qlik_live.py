import asyncio, json, sys, os
from playwright.async_api import async_playwright

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

async def run():
    print("Conectando ao Qlik Sense e extraindo estrutura da pasta Acompanhamento Categorias...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': 'lucas.alves6', 'password': 'Eloise2025*'}
        )
        page = await context.new_page()

        sheet_url = "https://sense.farmaciassaojoao.com.br/sense/app/671fa4f4-eb7d-418f-b4c9-936e87d8011d/sheet/ddd70c77-1a06-40d9-aff2-efa4b6b67b24/state/analysis"
        await page.goto(sheet_url, timeout=45000)
        await page.wait_for_timeout(10000)

        title = await page.title()

        qlik_info = await page.evaluate("""() => {
            const result = { objects: [] };
            const visualElements = document.querySelectorAll('.qv-object');
            visualElements.forEach((el, idx) => {
                const titleEl = el.querySelector('.qv-object-title-text, .qv-sub-title, .qv-object-title');
                const qid = el.getAttribute('data-qid') || el.id || '';
                const qtype = el.getAttribute('data-qtype') || el.getAttribute('class') || '';
                result.objects.push({
                    index: idx,
                    id: qid,
                    type: qtype,
                    title: titleEl ? titleEl.innerText.trim() : ''
                });
            });
            return result;
        }""")

        print("\n" + "=" * 70)
        print(f"  SUCCESS! Conectado ao Qlik Sense: {title}")
        print(f"  Total de objetos/tabelas na pasta: {len(qlik_info['objects'])}")
        print("=" * 70)
        for obj in qlik_info['objects']:
            print(f"  - [{obj['index']}] ID: {obj['id']} | Tipo: {obj['type'][:30]} | Título: '{obj['title']}'")
        print("=" * 70 + "\n")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
