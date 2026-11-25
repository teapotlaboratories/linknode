"""browse.py URL outprefix [wait_ms] - headless Chromium (existing Playwright build), saves text + screenshot."""
import sys,asyncio,glob
from playwright.async_api import async_playwright
url,out=sys.argv[1],sys.argv[2]; wait=int(sys.argv[3]) if len(sys.argv)>3 else 6000
exe=sorted(glob.glob('/home/argonite/.cache/ms-playwright/chromium-*/chrome-linux64/chrome'))[-1]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=exe,headless=True,args=['--disable-blink-features=AutomationControlled'])
        ctx=await b.new_context(user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',viewport={'width':1366,'height':1800},locale='en-US')
        pg=await ctx.new_page()
        r=await pg.goto(url,wait_until='domcontentloaded',timeout=60000)
        await pg.wait_for_timeout(wait)
        for _ in range(4):
            await pg.mouse.wheel(0,1500); await pg.wait_for_timeout(800)
        t=await pg.inner_text('body')
        open(out+'.txt','w').write(t)
        links=await pg.eval_on_selector_all('a[href]','els=>els.map(e=>[e.href,(e.innerText||"").slice(0,140).replace(/\\n/g," | ")])')
        open(out+'.links','w').write('\n'.join(h+'\t'+x for h,x in links))
        await pg.screenshot(path=out+'.png',full_page=False)
        print('status',r.status if r else None,'title',await pg.title(),'chars',len(t))
        await b.close()
asyncio.run(main())
