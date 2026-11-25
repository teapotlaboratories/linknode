import csv, json, sys
S=sys.argv[1]
rows=list(csv.DictReader(open(S+'/bom.csv')))
fps={x['ref']:x for x in json.load(open(S+'/fps.json'))}
def lc(c):
    try: return json.load(open(f'{S}/lcsc/{c}.json'))['result']
    except: return None
def jl(c):
    try:
        L=json.load(open(f'{S}/jlc/{c}.json'))['data']['componentPageInfo']['list']
        m=[x for x in L if x.get('componentCode')==c or (x.get('urlSuffix') or '').split('/')[-1]==c]
        return m[0] if m else None
    except: return None
def ladder(r,n):
    pl=sorted(r['productPriceList'],key=lambda p:p['ladder'])
    buy=max(n,pl[0]['ladder'],r.get('minBuyNumber') or 1)
    price=[p['usdPrice'] for p in pl if p['ladder']<=buy][-1]
    return price,buy
bom=[];excluded=[]
# merge lines by LCSC part number (PCBWay/LCSC buy per part number)
merged={}
for r in rows:
    refs=r['Refs'].split(',')
    if r['DNP']:
        excluded.append({'refs':refs,'value':r['Value'],'lcsc':r['LCSC'],'reason':'DNP (not fitted)'}); continue
    if r['Refs'].startswith('TP'):
        excluded.append({'refs':refs,'value':r['Value'],'lcsc':'','reason':'bare test-point pad (TestPoint_Pad_D1.0mm), no part placed'}); continue
    key=r['LCSC'] or r['Value']
    m=merged.setdefault(key,{'refs':[],'values':[],'lcsc':r['LCSC'],'qty':0,'footprint':r['Footprint']})
    m['refs']+=refs; m['values'].append(r['Value']); m['qty']+=int(r['Qty'])
for x in fps.values():
    if x['ref'].startswith('TP10') or x['ref'] in('J501',) or x['ref'].startswith('MH') or x['ref'].startswith('LOGO'):
        pass
excluded.append({'refs':[f'TP10{i:02d}' for i in range(1,36)],'value':'PogoPad_D1.5 expansion pads','lcsc':'','reason':'board-only copper pads (exclude-from-BOM in the board), no part placed'})
excluded.append({'refs':['J501'],'value':'DEBUG UART TestPads_1x03','lcsc':'','reason':'board-only copper pads, no part placed'})
excluded.append({'refs':['MH1','MH2','MH3','MH4'],'value':'MountingHole_3.2mm_M3','lcsc':'','reason':'mounting holes, no part'})
excluded.append({'refs':['LOGO1'],'value':'TeapotLogo','lcsc':'','reason':'silkscreen/copper graphic'})
HELTEC_URL='https://heltec.org/project/ht-hc01'
tot={10:{'pure':0,'moq':0},100:{'pure':0,'moq':0}}
for key,m in merged.items():
    side=sorted({fps[r]['side'] for r in m['refs'] if r in fps})
    line={'refs':m['refs'],'value':' / '.join(dict.fromkeys(m['values'])),'footprint':m['footprint'],'lcsc':m['lcsc'],'qty_per_board':m['qty'],'side':side}
    if m['lcsc']:
        r=lc(m['lcsc']); j=jl(m['lcsc'])
        p10,b10=ladder(r,m['qty']*10); p100,b100=ladder(r,m['qty']*100)
        line.update(unit_price_10=p10,unit_price_100=p100,buy_qty_10=b10,buy_qty_100=b100,
            mpn=r['productModel'],brand=r.get('brandNameEn'),lcsc_stock=r['stockNumber'],
            lcsc_price_ladder=[(p['ladder'],p['usdPrice']) for p in r['productPriceList']],
            jlc_library=(('basic' if j['componentLibraryType']=='base' else ('preferred extended' if j.get('preferredComponentFlag') else 'extended')) if j else 'unknown'),
            jlc_stock=(j['stockCount'] if j else None),
            source_url=f"https://www.lcsc.com/product-detail/{m['lcsc']}.html",
            api_url=f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={m['lcsc']}")
        notes=[]
        if r['stockNumber']==0: notes.append(f"LCSC stock 0 on 2026-11-23 (JLCPCB shows {j['stockCount'] if j else '?'} in stock)")
        if r['stockNumber'] < m['qty']*100: notes.append(f"LCSC stock {r['stockNumber']} < {m['qty']*100} needed for 100 boards")
        if b10>m['qty']*10: notes.append(f"qty-10 build must buy LCSC minimum {b10}")
        line['note']='; '.join(notes)
        for n,p,b in((10,p10,b10),(100,p100,b100)):
            tot[n]['pure']+=p*m['qty']; tot[n]['moq']+=p*b/n
        line['ext_per_board_10']=round(p10*m['qty'],4); line['ext_per_board_100']=round(p100*m['qty'],4)
        line['ext_per_board_10_with_moq']=round(p10*b10/10,4)
    else:
        line.update(unit_price_10=11.90,unit_price_100=11.90,mpn='HT-HC01 V2 (MM6108 + FEM, 27 dBm)',brand='Heltec',jlc_library='not at LCSC/JLCPCB',
            source_url=HELTEC_URL,note='No LCSC number. Heltec store price $11.90 (single-unit listing, no quantity tiers published); PCBWay turnkey cannot buy it from LCSC: expect to consign it (Combo) or have PCBWay source it from Heltec at an unknown markup. Shipping from Heltec not included.')
        for n in (10,100): tot[n]['pure']+=11.90*m['qty']; tot[n]['moq']+=11.90*m['qty']
        line['ext_per_board_10']=line['ext_per_board_100']=line['ext_per_board_10_with_moq']=11.90
    bom.append(line)
bom.sort(key=lambda l:-l['ext_per_board_100'])
fit=[x for x in fps.values() if not x['dnp'] and not x['exbom'] and not x['board_only'] and (x['smd'] or x['tht'])]
counts={'unique':len(merged),'bom_lines_by_value':sum(1 for r in rows if not r['DNP'] and not r['Refs'].startswith('TP')),
  'placements_total':len(fit),'placements_top':sum(1 for x in fit if x['side']=='top'),'placements_bottom':sum(1 for x in fit if x['side']=='bottom'),
  'smd_parts':sum(1 for x in fit if x['smd']),'smd_top':sum(1 for x in fit if x['smd'] and x['side']=='top'),'tht':sum(1 for x in fit if x['tht']),'tht_refs':[x['ref'] for x in fit if x['tht']],
  'joints':1071,'joints_detail':'1071 copper pads on fitted parts: 1044 SMD pads + 27 plated-hole pads (6 THT connector pins J2/J3/J4, 4 USB-C J1 shield legs, 17 thermal-via pads inside the U100 and U4 exposed-pad footprints); 1020 distinct pad numbers',
  'large_ic_count_for_pcbway':7,'large_ic_refs':['U100','U801','U701','U2','U20','J1','J401'],
  'source':'kicad-cli sch export bom + kicad-cli pcb export pos + pcbnew Python read of a scratch copy of linknode.kicad_pcb (2026-11-23)'}
QURL='https://www.pcbway.com/orderonline.aspx'
pcb={'spec':'FR-4 TG150, 4 layers, 78 x 62 mm, 1.6 mm, 1 oz outer / 0.5 oz inner, 4/4 mil class, 0.2 mm min hole, green/white, tented vias, single pieces, standard build time',
 'HASL lead free':{'5':32.20,'10':56.95,'100':166.27},'ENIG (Immersion gold)':{'5':62.04,'10':87.47,'100':197.95},
 'with impedance control (option)':{'HASL lead free':{'5':82.37,'10':105.51,'100':205.39},'ENIG':{'5':110.49,'10':135.37,'100':244.47}},
 'build_time':'4-5 days (qty 5, 10), 6-7 days (qty 100)',
 'source':'PCBWay instant-quote calculator, '+QURL+' (its backend https://www.pcbway.com/Quote/GetDeliveryDays/ queried with the form values above, 2026-11-23; raw replies in web/pcbway_pcb_quotes.json). Checked that the parameters are honoured: 2 layers = $19.22, 3/3 mil = $300.95, 0.15 mm via = $361.80 at qty 10.'}
SURL='https://www.pcbway.com/quotesmt.aspx'
assembly={'inputs':'Turnkey, single pieces, both sides, 89 unique parts, 298 SMD parts, 7 BGA/QFP-class parts (ICs > 16 pins, irregular parts > 10 pins), 3 THT parts',
 'fee_basis':'PCBWay quote form asks for counts of unique parts, SMD parts, BGA/QFP parts and through-hole parts (per part, not per joint); '+SURL,
 'assembly_service':{'5':279.69,'10':508.67,'100':1034.84},
 'assembly_service_kitted':{'5':372.92,'10':678.23,'100':1379.79},
 'sensitivity':{'top side only, qty 100':919.97,'0 BGA/QFP, qty 100':934.17,'0 THT, qty 100':1016.33,'qty 20':820.06,'qty 50':947.10,'qty 200':1242.01},
 'stencil':{'price_if_ordered':15.00,'note':'Stencil adds $15 when ordered (370 x 470 mm framework, queried); PCBWay states "PCBA provides free stencil" (https://www.pcbway.com/pcb-assembly.html) and the assembly quote shows no stencil line, so $0 is used. Budget $15-30 if they charge for top and bottom stencils.'},
 'promo_29':{'eligible':False,'why':'$29 offer is limited to max 200 components per board (this board has 301) and 20 boards; https://www.pcbway.com/blog/PCB_Design_Layout/How_to_Get_29_PCB_Assembly_and_Meet_the_Requirements_e334dbde.html'},
 'component_sourcing_markup':'Not published. The SMT quote states "Price does not include PCB fabrication or the cost of components" ('+SURL+'); parts are priced after BOM review. Industry markups 25-100%+ (Altium, https://resources.altium.com/p/what-every-pcb-buyer-should-know-about-buying-assemblies) are not PCBWay figures.',
 'excluded':'Customs duties and VAT not included (quotesmt.aspx notice). Shipping not published as a fixed rate: omitted.',
 'source':'PCBWay SMT instant-quote calculator '+SURL+' (backend /Quote/GetDeliveryDays/, 2026-11-23; raw replies in web/pcbway_smt_quotes.json, web/pcbway_smt_sensitivity.json)'}
def T(n,finish):
    comp=tot[n]['pure']; compm=tot[n]['moq']
    p=pcb[finish][str(n)]; a=assembly['assembly_service'][str(n)]
    return {'boards':n,'finish':finish,'components':round(comp*n,2),'components_with_lcsc_moq':round(compm*n,2),'pcb':p,'assembly':a,'stencil':0,
            'total':round(comp*n+p+a,2),'per_board':round((comp*n+p+a)/n,2),'per_board_components':round(comp,2),'per_board_components_with_moq':round(compm,2),
            'per_board_pcb':round(p/n,2),'per_board_assembly':round(a/n,2),
            'per_board_with_moq':round((compm*n+p+a)/n,2)}
totals={'qty10':T(10,'ENIG (Immersion gold)'),'qty100':T(100,'ENIG (Immersion gold)'),
        'qty10_HASL':T(10,'HASL lead free'),'qty100_HASL':T(100,'HASL lead free'),
        'note':'Components at LCSC price (no PCBWay markup, none published). ENIG is the headline because of the 0.35 mm-pitch QFN-128 (judgement, not a PCBWay requirement); HASL shown for comparison. Excludes shipping, duties/VAT, the PCBWay sourcing markup, the stencil, and the off-board items.'}
not_on_board=[
 {'item':'18650 Li-ion cells (parallel, wired to J3)','price':'not priced'},
 {'item':'Solar panel, ~6 V 2-3.5 W (user-supplied, P-11)','price':'not priced'},
 {'item':'Antennas: HaLow 915 MHz, GPS active antenna, ESP32-C5 2.4 GHz, plus U.FL pigtails','price':'not priced'},
 {'item':'Battery NTC MF52A103F3435 (C84036), taped to the cells, wired to J4','price':'LCSC $0.0544 (10+) / $0.0438 (100+)','source':'https://www.lcsc.com/product-detail/C84036.html'},
 {'item':'KF2EDGK-3.81-2P screw plug (C440858) shipped loose with J2','price':'LCSC $0.1535 (5+) / $0.1278 (50+) / $0.1147 (150+)','source':'https://www.lcsc.com/product-detail/C440858.html'},
 {'item':'Mating JST XH / PH housings and crimps for J3/J4, microSD card, enclosure','price':'not priced'}]
unverified=[
 'RV1106G3 price: live LCSC $23.867 (1+) / $21.1402 (30+), JLCPCB $23.6465 / $20.9449 (30+), stock 428 (LCSC) / 613 (JLCPCB). A web-search snippet of an older LCSC/JLCPCB index showed about $7.78 (1) / $5.33 (100+); that page could not be re-checked, so the current $21-24 is used. No published 100+ tier; Rockchip/agent pricing for volume is unknown. The G2 (C5272606) is $13.68 (1) / $10.90 (100).',
 'HT-HC01 V2 price $11.90 is the Heltec store single-unit price (https://heltec.org/project/ht-hc01); no volume tiers, no shipping; not stocked by LCSC, so PCBWay turnkey cannot source it from LCSC.',
 'PCBWay component sourcing markup or handling fee: not published; final PCBA price is set after BOM review.',
 'PCBWay instant quotes are estimates read from their calculator backend on 2026-11-23 (no account, default shipping country); PCBWay says the final price is subject to review. Confirm at https://www.pcbway.com/orderonline.aspx and https://www.pcbway.com/pcb-assembly.html.',
 'Stencil: assumed free with PCBA (PCBWay statement); $15 per stencil if charged.',
 'Shipping, customs duties and VAT: not published as fixed figures, not included.',
 'PCB spec assumptions: 1 oz outer / 0.5 oz inner copper, TG150, no impedance control, no via-in-pad/resin fill. If the RV1106 EP thermal vias or USB/RF lines need via-in-pad or impedance control, the PCB price rises (impedance control: $135.37 ENIG at qty 10, $244.47 at qty 100).',
 'J1 USB-C has 4 plated shield legs; counted as an SMD part (PCBWay may count it as THT: +$2.3 to +$4.6 per order in the sensitivity runs).',
 'Four basic passives (C19666, C19702, C307331, C23733) show LCSC stock 0 on 2026-11-23 but are in stock at JLCPCB; prices use the LCSC ladder.',
 'Attrition/spares (extra reels or loss parts a CM adds for 0402s) not included.',
 'Placement and joint counts come from the board as of 2026-11-23 while routing is in progress; parts may still change.']
out={'generated':'2026-11-23','currency':'USD','board':'LinkNode Rev 1, linknode.kicad_pcb','bom_lines':bom,'excluded':excluded,'counts':counts,'pcb':pcb,'assembly':assembly,'totals':totals,'not_on_board':not_on_board,'unverified':unverified}
json.dump(out,open(S+'/cost.json','w'),indent=1)
for k in ['qty10','qty100','qty10_HASL','qty100_HASL']: print(k,totals[k])
print(counts)
for l in bom[:12]: print(l['refs'][:4],l['value'],l['lcsc'],l['qty_per_board'],l['unit_price_10'],l['unit_price_100'],l['ext_per_board_10'],l['ext_per_board_100'],l.get('jlc_library'),l['note'][:80])
