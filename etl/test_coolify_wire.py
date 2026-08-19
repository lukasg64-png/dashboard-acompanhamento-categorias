import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://10.200.12.69:8000/login')
        await page.wait_for_selector('input[type="email"]')
        await page.fill('input[type="email"]', 'fsjplan.dados@gmail.com')
        await page.fill('input[type="password"]', 'ecommerce2026')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new')
        await page.wait_for_timeout(3000)
        
        # Encontrar os botões com wire:click ou texto
        buttons = await page.eval_on_selector_all('button', 'elements => elements.map(e => ({text: e.innerText.trim(), wire: e.getAttribute("wire:click"), class: e.className}))')
        print("Botões com wire:click:")
        for b in buttons:
            if b['wire']:
                print(" ->", b)

        # Clicar no botão de Private Git Repository ou Public Git Repository
        # Vamos tentar clicar no botão cujo wire:click cria private repository
        for b in buttons:
            if b['wire'] and ('private' in b['wire'].lower() or 'deploy' in b['wire'].lower() or 'settype' in b['wire'].lower() or 'repository' in b['wire'].lower()):
                print(f"Testando clique em: {b}")
                await page.click(f'button[wire\\:click="{b["wire"]}"]')
                await page.wait_for_timeout(3000)
                break

        await page.screenshot(path='coolify_after_click.png')
        text = await page.inner_text('body')
        print("Texto após clique:")
        print(text[:1000])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
