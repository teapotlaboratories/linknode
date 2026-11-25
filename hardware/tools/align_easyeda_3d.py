"""Align EasyEDA 3D models (fetched with easyeda2kicad) to the footprints actually used on the LinkNode board.
Usage: python3 align_easyeda_3d.py <board.kicad_pcb> <easy.pretty> REF=easy_footprint_name[@deg] [...]
@deg forces the rotation (use it for symmetric parts after checking pin 1); the translation then comes from the
numbered pads both footprints share (mean offset), so pin 1 lands on pin 1.
For each part: load EasyEDA's footprint (which carries the model offset/rotation that fits it) and our placed footprint
(at rotation 0, local frame). Find the rotation (0/90/180/270) and translation that put EasyEDA's copper pads on ours
(nearest-neighbour fit), then carry the model offset/rotation through the same transform. Prints the pad residual so the
fit can be judged; writes JSON {ref: {model, offset[x,y,z], rotate[x,y,z], residual_mm}} to stdout.
KiCad model offsets are in mm with +Y pointing up, opposite to footprint Y."""
import sys, json, math, re, pcbnew
board, epretty = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(board)
res = {}
def pads_local(fp):
    out = []
    o = fp.GetPosition(); a = math.radians(fp.GetOrientationDegrees())
    for p in fp.Pads():
        if not p.IsOnCopperLayer() or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
        dx, dy = (p.GetPosition().x - o.x)/1e6, (p.GetPosition().y - o.y)/1e6
        # undo footprint rotation (KiCad: screen y down, positive angle = CCW on screen)
        x = dx*math.cos(-a) + dy*math.sin(-a); y = -dx*math.sin(-a) + dy*math.cos(-a)
        out.append((x, y))
    return out
def rot(pt, deg):
    a = math.radians(deg); x, y = pt
    return (x*math.cos(a) + y*math.sin(a), -x*math.sin(a) + y*math.cos(a))
for arg in sys.argv[3:]:
    ref, ename = arg.split('=')
    force = None
    if '@' in ename: ename, force = ename.split('@'); force = int(force)
    ours = pads_local(b.FindFootprintByReference(ref))
    efp = pcbnew.FootprintLoad(epretty, ename)
    theirs = [((p.GetPosition().x)/1e6, (p.GetPosition().y)/1e6) for p in efp.Pads()
              if p.IsOnCopperLayer() and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    mdl = efp.Models()[0]
    best = None
    for deg in (0, 90, 180, 270):
        tr = [rot(p, deg) for p in theirs]
        # candidate translations: align each of their pads to each of ours for the pad nearest the centroid, then score
        cx = sum(p[0] for p in tr)/len(tr); cy = sum(p[1] for p in tr)/len(tr)
        anchor = min(tr, key=lambda p: (p[0]-cx)**2 + (p[1]-cy)**2)
        for q in ours:
            t = (q[0]-anchor[0], q[1]-anchor[1])
            d = [min(math.hypot(p[0]+t[0]-o[0], p[1]+t[1]-o[1]) for o in ours) for p in tr]
            d.sort(); score = sum(d[:max(1, int(len(d)*0.8))])/max(1, int(len(d)*0.8))   # ignore up to 20 % unmatched pads
            if best is None or score < best[0]: best = (score, deg, t)
    score, deg, t = best
    if force is not None:
        fpo = b.FindFootprintByReference(ref); o = fpo.GetPosition(); a = math.radians(fpo.GetOrientationDegrees())
        def loc(p):
            dx, dy = (p.GetPosition().x - o.x)/1e6, (p.GetPosition().y - o.y)/1e6
            return (dx*math.cos(-a) + dy*math.sin(-a), -dx*math.sin(-a) + dy*math.cos(-a))
        on = {p.GetNumber(): loc(p) for p in fpo.Pads() if p.GetNumber()}
        en = {p.GetNumber(): (p.GetPosition().x/1e6, p.GetPosition().y/1e6) for p in efp.Pads() if p.GetNumber()}
        common = [k for k in en if k in on]
        deg = force
        t = (sum(on[k][0] - rot(en[k], deg)[0] for k in common)/len(common), sum(on[k][1] - rot(en[k], deg)[1] for k in common)/len(common))
        score = sum(math.hypot(rot(en[k], deg)[0] + t[0] - on[k][0], rot(en[k], deg)[1] + t[1] - on[k][1]) for k in common)/len(common)
    # model offset (file frame: +Y up) -> footprint frame, transform, back
    ox, oy, oz = mdl.m_Offset.x, mdl.m_Offset.y, mdl.m_Offset.z
    fx, fy = rot((ox, -oy), deg); fx += t[0]; fy += t[1]
    rx, ry, rz = mdl.m_Rotation.x, mdl.m_Rotation.y, mdl.m_Rotation.z
    res[ref] = dict(model=mdl.m_Filename, offset=[round(fx, 4), round(-fy, 4), round(oz, 4)],
                    rotate=[rx, ry, (rz + deg) % 360], residual_mm=round(score, 4), pads=(len(ours), len(theirs)), fp_rot=deg)
print(json.dumps(res, indent=1))
