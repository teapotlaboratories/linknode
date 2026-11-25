"""List the interior corner angles of zone outlines (owner 2026-11-24: "no sharp edges"): flags convex corners < 90 deg and
concave corners > 270 deg. Usage: python3 zonecorners.py <board> PREFIX[,PREFIX...]"""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); bad_total = 0
for z in b.Zones():
    if not any(z.GetZoneName().startswith(p) for p in sys.argv[2].split(',')): continue
    o = z.Outline().Outline(0); P = [(o.CPoint(j).x/1e6, o.CPoint(j).y/1e6) for j in range(o.PointCount())]; n = len(P)
    sgn = 1 if sum(p[0]*q[1] - q[0]*p[1] for p, q in zip(P, P[1:] + P[:1])) > 0 else -1
    angs = []
    for k in range(n):
        a, v, c = P[k-1], P[k], P[(k+1) % n]
        u = (v[0]-a[0], v[1]-a[1]); w = (c[0]-v[0], c[1]-v[1])
        turn = math.degrees(math.atan2(u[0]*w[1] - u[1]*w[0], u[0]*w[0] + u[1]*w[1]))*sgn
        interior = 180 - turn; angs.append(round(interior))
        if interior < 89.5 or interior > 270.5: print(f'  {z.GetZoneName()} corner {k} at ({v[0]:.3f},{v[1]:.3f}): {interior:.0f} deg'); bad_total += 1
    print(z.GetZoneName(), n, 'corners, angles used:', sorted(set(angs)))
print('sharp corners:', bad_total)
