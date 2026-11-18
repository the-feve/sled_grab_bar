"""3D renders: handle on bar, and build stages. Geometry from the CAD numbers (mm)."""
import math, sys
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = sys.argv[1]
R = 4 * 25.4                    # arch CL radius (8" span, 4" rise)
BZ = 110.0                      # brace CL height (EST, from bar model)
A0 = math.asin(20.0 / R)        # core ends 20 mm above brace CL
CORE_R, CORD_R = 7.0, 2.0
COBRA_R, KING_R = 11.0, 15.2    # rung CL radii
BRACE_R = 7.5

def frame(t):
    c = np.array([R*math.cos(t), 0.0, BZ + R*math.sin(t)])
    N = np.array([math.cos(t), 0.0, math.sin(t)])      # outer edge of arch
    T = np.array([-math.sin(t), 0.0, math.cos(t)])
    B = np.array([0.0, 1.0, 0.0])                      # rider-side face
    return c, N, T, B

def tube(pts, r, sides=10):
    pts = np.asarray(pts, float)
    tris = []
    tang = np.gradient(pts, axis=0)
    tang /= np.linalg.norm(tang, axis=1)[:, None] + 1e-12
    ref = np.array([0.3, 0.9, 0.2])
    rings = []
    for p, t in zip(pts, tang):
        u = np.cross(t, ref);
        if np.linalg.norm(u) < 1e-6: u = np.cross(t, [1, 0, 0])
        u /= np.linalg.norm(u); v = np.cross(t, u)
        a = np.linspace(0, 2*np.pi, sides, endpoint=False)
        rings.append(p + r*(np.outer(np.cos(a), u) + np.outer(np.sin(a), v)))
        ref = u
    for i in range(len(rings)-1):
        A, Bq = rings[i], rings[i+1]
        for j in range(sides):
            k = (j+1) % sides
            tris.append([A[j], A[k], Bq[k], Bq[j]])
    return tris

def sweep_core(t0, t1, n=120):
    """core as a tube along the arch (grooves too small to see at this scale)"""
    return tube([frame(t)[0] for t in np.linspace(t0, t1, n)], CORE_R, 20)

def strands(t0, t1):
    out = []
    for ang in (45, 135, 225, 315):
        a = math.radians(ang); pts = []
        for t in np.linspace(t0, t1, 120):
            c, N, T, B = frame(t)
            pts.append(c + 6.6*(math.cos(a)*N + math.sin(a)*B))
        out.append(pts)
    return out

def loops(side):
    """front-groove cord -> loop around the RISER just above the clamp;
    back-groove cord -> loop around the CROSS BRACE. 2 legs each."""
    t = A0 if side > 0 else math.pi - A0
    c, N, T, B = frame(t)
    res = []
    # riser axis (from bar model: bottom vertex x=86 at z=0, riser top x=150 at z=178)
    d = np.array([side*64.0, 0.0, 178.0]); d /= np.linalg.norm(d)
    zr = 128.0; rc = np.array([side*(86 + 64*zr/178), 0.0, zr])
    u = np.array([0.0, 1.0, 0.0]); v = np.cross(d, u)
    rr = 11.1 + CORD_R
    riser_ring = [rc + rr*(math.cos(q)*u + math.sin(q)*v) for q in np.linspace(0, 2*np.pi, 40)]
    brace_ring = [np.array([side*R, (BRACE_R+CORD_R)*math.sin(q), BZ + (BRACE_R+CORD_R)*math.cos(q)])
                  for q in np.linspace(0, 2*np.pi, 40)]
    res += [riser_ring, brace_ring]
    for (a1, a2), ring in (((45, 135), riser_ring), ((225, 315), brace_ring)):
        for a in (a1, a2):
            aa = math.radians(a)
            p0 = c + 6.6*(math.cos(aa)*N + math.sin(aa)*B)
            p1 = min(ring, key=lambda q: np.linalg.norm(q - p0))
            res.append([p0 + (p1-p0)*k for k in np.linspace(0, 1, 8)])
    return res

def cobra(t0, t1, rr, pitch, colors):
    """rungs across both faces, loops at both edges. pitch = arc length per knot on CL"""
    dt = pitch / R
    out = []
    t, k = t0, 0
    while t + dt <= t1:
        pts = []
        # front rung inner edge -> outer edge, back rung outer -> inner, edge loops bulge out
        for u in np.linspace(-90, 90, 13):
            c, N, T, B = frame(t)
            a = math.radians(u)
            pts.append(c + rr*(math.sin(a)*N + math.cos(a)*B))
        for u in np.linspace(90, 270, 13):
            tt = t + dt*0.5*(u-90)/180
            c, N, T, B = frame(tt)
            a = math.radians(u)
            bulge = 1.0 + 0.18*math.exp(-((u-90)/25)**2)
            pts.append(c + rr*bulge*(math.sin(a)*N + math.cos(a)*B))
        for u in np.linspace(270, 450, 7)[1:4]:
            tt = t + dt*0.5 + dt*0.5*(u-270)/180
            c, N, T, B = frame(tt)
            a = math.radians(u)
            pts.append(c + rr*1.18*(math.sin(a)*N + math.cos(a)*B))
        out.append((pts, colors[k % len(colors)]))
        t += dt; k += 1
    return out

def bar_mesh(skip_old_handle=True):
    asm = cq.importers.importStep(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "cad", "rmk_bar_2883837.step"))
    polys = []
    for s in asm.val().Solids():
        bb = s.BoundingBox()
        if skip_old_handle and bb.zmax > 150 and abs(bb.xmax) < 160 and abs(bb.xmin) < 160:
            continue          # old arch
        if skip_old_handle and bb.xlen < 25 and bb.ylen > 10 and abs(bb.center.y) > 3 and bb.zlen < 25:
            continue          # old pivot bosses
        v, t = s.tessellate(0.4)
        cx = abs(bb.center.x)
        dark = cx > 250 or (bb.xlen < 45 and bb.zlen < 45 and 100 < cx < 160)
        col = "#2b2b2b" if dark else "#9a9ca0"
        for f in t:
            polys.append(([np.array([v[i].x, v[i].y, v[i].z]) for i in f], col))
    return polys

def shade(polys, light=np.array([0.4, 0.8, 0.6])):
    light = light/np.linalg.norm(light)
    verts, cols = [], []
    for p, col in polys:
        p = np.asarray(p)
        n = np.cross(p[1]-p[0], p[2]-p[0]); nn = np.linalg.norm(n)
        if nn < 1e-9: continue
        n /= nn
        lam = 0.38 + 0.62*abs(np.dot(n, light))
        rgb = np.array(matplotlib.colors.to_rgb(col))*lam
        verts.append(p); cols.append(np.clip(rgb, 0, 1))
    return verts, cols

ZOOM = 1.0
def render(polys, fn, lims, elev, azim, size=(10, 7), zoom=1.0):
    global ZOOM; ZOOM = zoom
    verts, cols = shade(polys)
    fig = plt.figure(figsize=size)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(verts, facecolors=cols, edgecolors=cols, linewidths=0.2))
    (x0, x1), (y0, y1), (z0, z1) = lims
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1)
    ax.set_box_aspect((x1-x0, y1-y0, z1-z0), zoom=ZOOM)
    ax.view_init(elev, azim); ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    plt.savefig(fn, dpi=130, facecolor="white"); plt.close(fig)

ORANGE, BLACK, BLUE, CORE = "#f26a1b", "#262626", "#2f6fd0", "#4fc4a0"

def handle(stage):
    """stage 1 core+strands, 2 +cobra, 3 +king cobra (finished), 'cut' = staged cutaway"""
    P = []
    t0, t1 = A0, math.pi - A0
    P += [(q, CORE) for q in sweep_core(t0, t1)]
    for s in strands(t0, t1): P += [(q, BLUE) for q in tube(s, CORD_R, 8)]
    for side in (1, -1):
        for l in loops(side): P += [(q, BLUE) for q in tube(l, CORD_R, 8)]
    if stage == "cut":
        cob_end, king_end = 0.70*math.pi, 0.45*math.pi
    else:
        cob_end = t1 if stage >= 2 else None
        king_end = t1 if stage >= 3 else None
    if cob_end:
        for pts, col in cobra(t0, cob_end, COBRA_R, 3.7, [BLACK]):
            P += [(q, col) for q in tube(pts, CORD_R, 8)]
    if king_end:
        for pts, col in cobra(t0, king_end, KING_R, 3.9, [ORANGE]):
            P += [(q, col) for q in tube(pts, CORD_R, 8)]
    return P

bar = bar_mesh()
full = bar + handle(3)
render(full, f"{OUT}/render_full_bar.png", ((-430, 430), (-80, 120), (-30, 260)), 16, 62, (14, 5.5), 1.2)
close_lims = ((-150, 150), (-60, 60), (70, 250))
render(bar + handle("cut"), f"{OUT}/render_build_stages.png", close_lims, 12, 72, (10, 7), 1.25)
for st in (1, 2, 3):
    render(bar + handle(st), f"{OUT}/render_stage{st}.png", close_lims, 12, 72, (7, 5), 1.25)
print("done")
