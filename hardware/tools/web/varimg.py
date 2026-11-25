"""varimg.py URL outdir prefix "title1" "title2"... - select each SKU variant and screenshot the main product image."""
import sys,asyncio,glob,os,json
from playwright.async_api import async_playwright
url,outd,prefix=sys.argv[1],sys.argv[2],sys.argv[3]; titles=sys.argv[4:]
exe=sorted(glob.glob('/home/argonite/.cache/ms-playwright/chromium-*/chrome-linux64/chrome'))[-1]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=exe,headless=True,args=['--disable-blink-features=AutomationControlled'])
        ctx=await b.new_context(user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',viewport={'width':1366,'height':1800},locale='en-US')
        pg=await ctx.new_page(); await pg.goto(url,wait_until='domcontentloaded',timeout=60000); await pg.wait_for_timeout(8000)
        out=[]
        cands=['[class*="magnifier--wrap"]','[class*="image-view--previewBox"]','[class*="magnifier"]','[class*="image-view"]']
        box=None
        for c in cands:
            box=await pg.query_selector(c)
            if box: break
        print('image box selector',c if box else None)
        thumbs=await pg.evaluate("()=>Array.from(document.querySelectorAll('[class*=\"slider--img\"] img, [class*=\"image-view--previewWrap\"] img')).map(i=>i.currentSrc||i.src)")
        for k,t in enumerate(titles):
            norm=t.replace(' ','').lower()
            ok=await pg.evaluate('''(n)=>{const els=[...document.querySelectorAll('[class*="sku-item--image"],[class*="sku-item--text"],[data-sku-col]')];
                const e=els.find(x=>((x.getAttribute('title')||x.innerText||'').replace(/\\s/g,'').toLowerCase())===n); if(e){e.click();return true} return false}''',norm)
            if not ok: print('missing',t); continue
            await pg.wait_for_timeout(1800)
            src=await pg.evaluate("()=>{const i=document.querySelector('[class*=\"magnifier--image\"]')||document.querySelector('[class*=\"image-view--previewBox\"] img');return i?(i.currentSrc||i.src):''}")
            fn=f'{prefix}_v{k:02d}.png'
            if box: await box.screenshot(path=os.path.join(outd,fn))
            out.append(dict(title=t,file=fn,src=src))
            print(t,'->',fn,src[:90])
        json.dump(dict(variants=out,thumbs=thumbs),open(os.path.join(outd,prefix+'_variants.json'),'w'),indent=1)
        await b.close()
asyncio.run(main())
