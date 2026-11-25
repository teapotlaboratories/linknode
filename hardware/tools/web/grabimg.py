"""grabimg.py URL prefix outdir - save the product images of a page (AliExpress SKU thumbnails + og:image / gallery)."""
import sys,asyncio,glob,json,re,os
from playwright.async_api import async_playwright
url,prefix,outd=sys.argv[1],sys.argv[2],sys.argv[3]
exe=sorted(glob.glob('/home/argonite/.cache/ms-playwright/chromium-*/chrome-linux64/chrome'))[-1]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=exe,headless=True,args=['--disable-blink-features=AutomationControlled'])
        ctx=await b.new_context(user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',viewport={'width':1366,'height':1800},locale='en-US')
        pg=await ctx.new_page(); await pg.goto(url,wait_until='domcontentloaded',timeout=60000); await pg.wait_for_timeout(8000)
        found=await pg.evaluate("""()=>{
          const out=[];
          document.querySelectorAll('[class*="sku-item--image"]').forEach(e=>{const i=e.querySelector('img');if(i)out.push({kind:'sku',title:e.getAttribute('title')||i.alt||'',src:i.currentSrc||i.src})});
          const og=document.querySelector('meta[property="og:image"]'); if(og)out.push({kind:'og',title:'og',src:og.content});
          document.querySelectorAll('[class*="magnifier--image"], [class*="image-view--previewBox"] img, img[class*="magnifier"], .product-photo img, img[data-testid*="product"], img[alt*="Product"]').forEach(i=>out.push({kind:'main',title:i.alt||'',src:i.currentSrc||i.src}));
          return out}""")
        res=[];seen=set()
        for k,f in enumerate(found):
            src=re.sub(r'_\d+x\d+\.(jpg|png|webp|avif).*$','',f['src'])
            src=re.sub(r'(\.(jpg|png|jpeg))_.*$',r'\1',src)
            if not src or src in seen or src.startswith('data:'): continue
            seen.add(src)
            try:
                r=await ctx.request.get(src if src.startswith('http') else 'https:'+src,timeout=30000)
                if r.ok:
                    ct=r.headers.get('content-type','')
                    ext='png' if 'png' in ct else 'webp' if 'webp' in ct else 'avif' if 'avif' in ct else 'jpg'
                    fn=f"{prefix}_{len(res):02d}.{ext}"; open(os.path.join(outd,fn),'wb').write(await r.body())
                    res.append(dict(file=fn,kind=f['kind'],title=f['title'],src=src,ct=ct))
            except Exception as e: print('ERR',src[:80],e)
        json.dump(res,open(os.path.join(outd,prefix+'.json'),'w'),indent=1); print(prefix,len(res),'images')
        await b.close()
asyncio.run(main())
