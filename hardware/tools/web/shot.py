import asyncio,glob,sys
from playwright.async_api import async_playwright
exe=sorted(glob.glob('/home/argonite/.cache/ms-playwright/chromium-*/chrome-linux64/chrome'))[-1]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=exe,headless=True)
        pg=await b.new_page(viewport={'width':1200,'height':900})
        msgs=[];pg.on('console',lambda m:msgs.append(m.text)); pg.on('pageerror',lambda e:msgs.append(str(e)))
        await pg.goto('file://'+sys.argv[1]); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=sys.argv[2],full_page=True); print('console',msgs)
        await b.close()
asyncio.run(main())
