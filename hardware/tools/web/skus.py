"""skus.py ITEM_URL out.json - click each SKU variant on an AliExpress item page and record its title and price."""
import sys,asyncio,glob,json,re
from playwright.async_api import async_playwright
url,out=sys.argv[1],sys.argv[2]
exe=sorted(glob.glob('/home/argonite/.cache/ms-playwright/chromium-*/chrome-linux64/chrome'))[-1]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=exe,headless=True,args=['--disable-blink-features=AutomationControlled'])
        ctx=await b.new_context(user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',viewport={'width':1366,'height':1800},locale='en-US')
        pg=await ctx.new_page(); await pg.goto(url,wait_until='domcontentloaded',timeout=60000); await pg.wait_for_timeout(8000)
        items=await pg.query_selector_all('[class*="sku-item--image"], [class*="sku-item--text"], [data-sku-col]')
        print('sku elements',len(items))
        res=[]
        for el in items:
            try:
                title=(await el.get_attribute('title')) or (await el.inner_text()) or ''
                img=await el.query_selector('img')
                if not title and img: title=await img.get_attribute('alt') or ''
                await el.evaluate("e=>e.click()"); await pg.wait_for_timeout(900)
                pr=await pg.query_selector('[class*="price-default--current"], [class*="price--current"], [class*="product-price-current"]')
                ptxt=(await pr.inner_text()).strip() if pr else ''
                orig=await pg.query_selector('[class*="price-default--original"], [class*="price--original"]')
                otxt=(await orig.inner_text()).strip() if orig else ''
                sel=await pg.query_selector('[class*="sku-title"]')
                stxt=(await sel.inner_text()).strip() if sel else ''
                res.append(dict(title=title.strip(),price=ptxt,original=otxt,selected=stxt))
            except Exception as e:
                res.append(dict(title='ERR',err=str(e)[:80]))
        json.dump(res,open(out,'w'),indent=1); print(len(res),'variants')
        await b.close()
asyncio.run(main())
