"""2D drawings generated from the model numbers (mm).
1) drawing_front_dimensioned.svg : front view to scale + section A-A
2) cobra_knot_steps.svg          : knot sequence with true over/under layering
"""
import math, sys
OUT = sys.argv[1]
IN = 25.4
FONT = 'font-family="Helvetica, Arial, sans-serif"'

# ---------------- model numbers (match cad/rmk_bar.py and cad/tpu_core.py) ----------
BAR_OD, CLAMP_HALF, BOT_R, RISE, RTX, UP_R, GRIP_X, UPSWEEP = 22.2, 56, 30, 178, 150, 55, 395, 12
GRIP_OD, GRIP_LEN, HOOK_R, HOOK_DROP = 32, 140, 18, 65
BZ, BRACE_OD, COL_OD, COL_LEN = 110, 15, 34, 26
R = 4 * IN; A0 = math.asin(20 / R); BRAID_OD = 34; CORE_D = 14

def fillet_path(pts, radii):
    """2D polyline with tangent arcs -> list of points"""
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        (ax, ay), (bx, by), (cx, cy) = pts[i-1], pts[i], pts[i+1]
        u1 = ((ax-bx), (ay-by)); l1 = math.hypot(*u1); u1 = (u1[0]/l1, u1[1]/l1)
        u2 = ((cx-bx), (cy-by)); l2 = math.hypot(*u2); u2 = (u2[0]/l2, u2[1]/l2)
        th = math.acos(max(-1, min(1, u1[0]*u2[0]+u1[1]*u2[1])))
        r = radii[i-1]; t = r/math.tan(th/2)
        p1 = (bx+u1[0]*t, by+u1[1]*t); p2 = (bx+u2[0]*t, by+u2[1]*t)
        bis = (u1[0]+u2[0], u1[1]+u2[1]); lb = math.hypot(*bis); bis = (bis[0]/lb, bis[1]/lb)
        cen = (bx+bis[0]*r/math.sin(th/2), by+bis[1]*r/math.sin(th/2))
        a1 = math.atan2(p1[1]-cen[1], p1[0]-cen[0]); a2 = math.atan2(p2[1]-cen[1], p2[0]-cen[0])
        d = (a2-a1+math.pi) % (2*math.pi) - math.pi
        for k in range(13):
            a = a1 + d*k/12
            out.append((cen[0]+r*math.cos(a), cen[1]+r*math.sin(a)))
    out.append(pts[-1])
    return out

# ---------------- 1) front view -----------------------------------------------------
S = 0.70                       # px per mm
OX, OZ = 340, 245              # px of model origin (clamp CL)
def P(x, z): return (OX + x*S, OZ - z*S)
def pts_d(pts): return "M" + " L".join(f"{P(*p)[0]:.1f} {P(*p)[1]:.1f}" for p in pts)

bx = CLAMP_HALF + BOT_R
right = [(bx, 0), (RTX, RISE), (GRIP_X, RISE+UPSWEEP)]
bar = [(-x, z) for x, z in reversed(right)] + right
bar_cl = fillet_path(bar, [UP_R, BOT_R, BOT_R, UP_R])
gdx, gdz = GRIP_X-RTX, UPSWEEP; gl = math.hypot(gdx, gdz); gd = (gdx/gl, gdz/gl)
lean = math.atan2(RTX-bx, RISE)
brace_x = bx + (RTX-bx)*BZ/RISE

svg = []
A = svg.append
H = 510
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="680" height="{H}" viewBox="0 0 680 {H}">')
A(f'<rect width="680" height="{H}" fill="#fff"/>')
A('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 1L9 5L0 9z" fill="#333"/></marker>'
  '<marker id="e" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 1L9 5L0 9z" fill="#b5651d"/></marker></defs>')

def tubeline(pts, od, fill, edge="#3a3a3a"):
    d = pts_d(pts)
    A(f'<path d="{d}" fill="none" stroke="{edge}" stroke-width="{od*S+1.6:.1f}" stroke-linecap="butt" stroke-linejoin="round"/>')
    A(f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{od*S:.1f}" stroke-linecap="butt" stroke-linejoin="round"/>')

# brace (behind bar)
tubeline([(-brace_x, BZ), (brace_x, BZ)], BRACE_OD, "#b9bbbe")
tubeline(bar_cl, BAR_OD, "#c9cbce")
for sx in (1, -1):
    e = (sx*GRIP_X, RISE+UPSWEEP); d = (sx*gd[0], gd[1])
    tubeline([(e[0]-d[0]*GRIP_LEN, e[1]-d[1]*GRIP_LEN), e], GRIP_OD, "#2b2b2b", "#111")
    hook = fillet_path([(e[0]-d[0]*20, e[1]-d[1]*20), (e[0]+d[0]*HOOK_R, e[1]+d[1]*HOOK_R),
                        (e[0]+d[0]*HOOK_R, e[1]+d[1]*HOOK_R-HOOK_DROP)], [HOOK_R])
    tubeline(hook, BAR_OD, "#2b2b2b", "#111")
    # brace clamp collar, rotated with riser
    cx, cz = sx*brace_x, BZ; ang = -sx*lean
    corners = []
    for u, v in ((-COL_OD/2, -COL_LEN/2), (COL_OD/2, -COL_LEN/2), (COL_OD/2, COL_LEN/2), (-COL_OD/2, COL_LEN/2)):
        corners.append((cx + u*math.cos(ang) - v*math.sin(ang), cz + u*math.sin(ang) + v*math.cos(ang)))
    A(f'<path d="{pts_d(corners)}Z" fill="#2b2b2b" stroke="#111" stroke-width="1"/>')

# handle: braid along arch, legs, loops (rings seen edge-on)
arch = [(R*math.cos(A0+(math.pi-2*A0)*k/80), BZ + R*math.sin(A0+(math.pi-2*A0)*k/80)) for k in range(81)]
for sx in (1, -1):
    xe = sx*R*math.cos(A0)
    # brace loop (back cord): ring around brace, seen edge-on
    A(f'<path d="{pts_d([(xe, BZ+20), (sx*R, BZ+BRACE_OD/2+2)])}" stroke="#2f6fd0" stroke-width="{4*S+0.5:.1f}" fill="none"/>')
    x0, y0 = P(sx*R, BZ+BRACE_OD/2+4); x1, y1 = P(sx*R, BZ-BRACE_OD/2-4)
    A(f'<rect x="{x0-2*S:.1f}" y="{y0:.1f}" width="{4*S:.1f}" height="{y1-y0:.1f}" fill="#2f6fd0" stroke="#1d4c96" stroke-width="0.6"/>')
    # riser loop (front cord): ring around riser just above the clamp, seen edge-on across the riser
    zr = 128.0; xr = sx*(bx + (RTX-bx)*zr/RISE)
    nx, nz = math.cos(lean)*sx, -math.sin(lean)      # across the riser
    rr = BAR_OD/2 + 3
    A(f'<path d="{pts_d([(xe, BZ+22), (xr - nx*rr, zr - nz*rr)])}" stroke="#2f6fd0" stroke-width="{4*S+0.5:.1f}" fill="none"/>')
    A(f'<path d="{pts_d([(xr - nx*rr, zr - nz*rr), (xr + nx*rr, zr + nz*rr)])}" stroke="#1d4c96" stroke-width="{4*S+2:.1f}" fill="none"/>')
    A(f'<path d="{pts_d([(xr - nx*rr, zr - nz*rr), (xr + nx*rr, zr + nz*rr)])}" stroke="#2f6fd0" stroke-width="{4*S:.1f}" fill="none"/>')
tubeline(arch, BRAID_OD, "#f26a1b", "#a8430c")
A(f'<path d="{pts_d(arch)}" fill="none" stroke="#7a2e07" stroke-width="0.8" stroke-dasharray="6 4"/>')

# dimensions
def text(x, y, s, anchor="middle", col="#222", size=12, weight=400):
    A(f'<text x="{x:.1f}" y="{y:.1f}" {FONT} font-size="{size}" font-weight="{weight}" fill="{col}" text-anchor="{anchor}">{s}</text>')
def hdim(x1, x2, z, label, est=False, ext_from=None, below=False):
    col = "#b5651d" if est else "#333"; mk = "e" if est else "a"
    a, y = P(x1, z); b, _ = P(x2, z)
    if ext_from is not None:
        for x, zf in ((x1, ext_from[0]), (x2, ext_from[1])):
            px, pz = P(x, zf)
            A(f'<line x1="{px:.1f}" y1="{pz:.1f}" x2="{px:.1f}" y2="{y + (4 if pz < y else -4):.1f}" stroke="{col}" stroke-width="0.6"/>')
    A(f'<line x1="{a:.1f}" y1="{y:.1f}" x2="{b:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="0.9" marker-start="url(#{mk})" marker-end="url(#{mk})"/>')
    text((a+b)/2, y + (14 if below else -5), label, col=col)
def vdim(x, z1, z2, label, est=False, side="right", yoff=0):
    col = "#b5651d" if est else "#333"; mk = "e" if est else "a"
    px, a = P(x, z1); _, b = P(x, z2)
    A(f'<line x1="{px:.1f}" y1="{a:.1f}" x2="{px:.1f}" y2="{b:.1f}" stroke="{col}" stroke-width="0.9" marker-start="url(#{mk})" marker-end="url(#{mk})"/>')
    lines = label.split("|")
    for i, ln in enumerate(lines):
        text(px + (6 if side == "right" else -6), (a+b)/2 + 4 + yoff + (i-(len(lines)-1)/2)*14, ln, "start" if side == "right" else "end", col)

hdim(-R, R, 82, "8.0 in span (loop to loop)", ext_from=(BZ-BRACE_OD/2-5, BZ-BRACE_OD/2-5), below=True)
vdim(-6, BZ, BZ+R, "4.0 in|rise", side="left", yoff=14)
vdim(10, BZ+BRACE_OD/2, BZ+R-BRAID_OD/2, "3.0 in|gap", yoff=2)
hook_out = GRIP_X + gd[0]*HOOK_R + BAR_OD/2
vdim(300, 0, RISE, "7 in bar rise|(published)", side="right", yoff=10)
A(f'<line x1="{P(bx,0)[0]+12:.1f}" y1="{P(0,0)[1]:.1f}" x2="{P(304,0)[0]:.1f}" y2="{P(0,0)[1]:.1f}" stroke="#333" stroke-width="0.5" stroke-dasharray="4 3"/>')
vdim(-(GRIP_X-80), 0, BZ, "4.3 in brace|height (EST)", est=True, side="left")
A(f'<line x1="{P(-(GRIP_X-84),BZ)[0]:.1f}" y1="{P(0,BZ)[1]:.1f}" x2="{P(-brace_x-20,BZ)[0]:.1f}" y2="{P(0,BZ)[1]:.1f}" stroke="#b5651d" stroke-width="0.5" stroke-dasharray="4 3"/>')
A(f'<line x1="{P(-(GRIP_X-84),0)[0]:.1f}" y1="{P(0,0)[1]:.1f}" x2="{P(-bx-12,0)[0]:.1f}" y2="{P(0,0)[1]:.1f}" stroke="#b5651d" stroke-width="0.5" stroke-dasharray="4 3"/>')
hdim(-brace_x, brace_x, -32, f"{2*brace_x/IN:.1f} in brace clamp centers (EST)", est=True, ext_from=(BZ-COL_LEN/2-4, BZ-COL_LEN/2-4), below=True)
hdim(-hook_out, hook_out, -68, f"{2*hook_out/IN:.1f} in overall (EST)", est=True, ext_from=(RISE+UPSWEEP-HOOK_DROP-6, RISE+UPSWEEP-HOOK_DROP-6), below=True)
# leader: core end gap
lx, lz = P(R*math.cos(A0)+8, BZ+20)
A(f'<line x1="{lx:.1f}" y1="{lz:.1f}" x2="528" y2="{lz-95:.1f}" stroke="#555" stroke-width="0.6" stroke-dasharray="3 3"/>')
text(532, lz-118, "Core ends 0.8 in", "start", "#333")
text(532, lz-104, "above brace CL", "start", "#333")
text(532, lz-86, "Blue loops, each end:", "start", "#1d4c96")
text(532, lz-72, "1 on riser above clamp", "start", "#1d4c96")
text(532, lz-58, "1 on cross brace", "start", "#1d4c96")

# section A-A at 3:1
SX, SY, K = 150, 415, 3.0
A(f'<circle cx="{SX}" cy="{SY}" r="{17*K}" fill="#f26a1b" stroke="#a8430c" stroke-width="1"/>')
A(f'<circle cx="{SX}" cy="{SY}" r="{13*K}" fill="#2b2b2b"/>')
A(f'<circle cx="{SX}" cy="{SY}" r="{9*K}" fill="#555"/>')
A(f'<circle cx="{SX}" cy="{SY}" r="{7*K}" fill="#4fc4a0" stroke="#2a8a6c" stroke-width="1"/>')
for ang in (45, 135, 225, 315):
    a = math.radians(ang)
    A(f'<circle cx="{SX+6.6*K*math.cos(a):.1f}" cy="{SY-6.6*K*math.sin(a):.1f}" r="{2*K}" fill="#2f6fd0" stroke="#1d4c96" stroke-width="0.8"/>')
A(f'<rect x="{SX-3*K}" y="{SY+7*K-0.8*K}" width="{6*K}" height="{0.8*K}" fill="#fff"/>')
text(SX, SY-17*K-10, "Section A-A (3x scale)", weight=500, size=13)
for i, (lab, r) in enumerate((("Outer layer, about 1.3 in OD", 15.2), ("Inner cobra layer", 11), ("Core strands, 4 legs", 6.6), ("TPU core, 14 mm", 3))):
    yy = SY - 30 + i*20
    A(f'<line x1="{SX + r*K*0.7:.1f}" y1="{SY - r*K*0.7 + (i*6 if i>1 else 0):.1f}" x2="{SX+75}" y2="{yy-4}" stroke="#555" stroke-width="0.6" stroke-dasharray="3 3"/>')
    text(SX+80, yy, lab, "start")
text(SX, SY+17*K+18, "Flat face is the print-bed side", size=11, col="#555")

# notes
NX = 400
NY = -70
text(NX, 448+NY, "Front view from the rider seat, to scale", "start", weight=500, size=13)
text(NX, 468+NY, "Black = known or measured", "start")
text(NX, 486+NY, "Orange text = estimate from photos", "start", "#b5651d")
text(NX, 504+NY, "Blue = core strands and loops", "start", "#1d4c96")
text(NX, 522+NY, "Dashed line = TPU core centerline", "start")
text(NX, 548+NY, "Scale bar:", "start")
A(f'<rect x="{NX+62}" y="{540+NY}" width="{IN*S*2:.1f}" height="6" fill="#333"/>')
text(NX+62+IN*S*2+6, 548+NY, "2 in", "start")
A('</svg>')
open(f"{OUT}/drawing_front_dimensioned.svg", "w").write("\n".join(svg))

# ---------------- 2) cobra knot steps ---------------------------------------------
OR, ORD = "#f26a1b", "#a8430c"     # cord 1
PU, PUD = "#7a4fd0", "#45288f"     # cord 2
W = 13                             # cord stroke

panels = []
def cord(d, c, cd):
    return (f'<path d="{d}" fill="none" stroke="{cd}" stroke-width="{W+3}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{W}" stroke-linecap="round" stroke-linejoin="round"/>')
def core(y0=20, y1=232):
    return (f'<rect x="86" y="{y0}" width="28" height="{y1-y0}" rx="6" fill="#4fc4a0" stroke="#2a8a6c" stroke-width="1.2"/>'
            f'<line x1="93" y1="{y0+4}" x2="93" y2="{y1-4}" stroke="#2f6fd0" stroke-width="3"/>'
            f'<line x1="107" y1="{y0+4}" x2="107" y2="{y1-4}" stroke="#2f6fd0" stroke-width="3"/>')
def knot_block(y, front=OR, fd=ORD, edge=PU, ed=PUD):
    return (cord(f"M70 {y} L130 {y}", front, fd)
            + f'<ellipse cx="70" cy="{y+2}" rx="9" ry="8" fill="{edge}" stroke="{ed}" stroke-width="1.5"/>'
            + f'<ellipse cx="130" cy="{y+2}" rx="9" ry="8" fill="{edge}" stroke="{ed}" stroke-width="1.5"/>')

# P1: middle of cord behind the core
p = cord("M60 230 L60 52 Q60 40 72 40 L100 40", OR, ORD) + cord("M100 40 L128 40 Q140 40 140 52 L140 230", PU, PUD) + core()
panels.append((p, ["1. Put the middle of the", "cord behind the core."]))
# P2: left cord over the front, tail hangs between core and right cord
p = (cord("M100 40 L128 40 Q140 40 140 52 L140 230", PU, PUD) + cord("M100 40 L72 40 Q60 40 60 52", OR, ORD) + core()
     + cord("M60 52 L60 92 Q60 108 76 108 L118 108 Q126 108 126 120 L126 230", OR, ORD))
panels.append((p, ["2. Left cord goes OVER the", "front. Leave a loop on the left."]))
# P3: right cord over the tail, behind the core, up through the loop
def step3(L, Ld, Rc, Rd, top=True):
    return ((cord("M100 40 L72 40 Q60 40 60 52", L, Ld) if top else "")
     + cord("M100 40 L128 40 Q140 40 140 52 L140 120", Rc, Rd)
     + cord("M86 150 L80 150 Q70 150 71 135 L72 98", Rc, Rd)        # behind core, under the loop bottom
     + core()
     + cord("M60 52 L60 92 Q60 108 76 108 L118 108 Q126 108 126 120 L126 230", L, Ld)
     + cord("M140 120 Q142 150 120 150 L114 150", Rc, Rd)             # over the tail
     + cord("M72 98 L74 64", Rc, Rd))                                 # comes out the front, inside the loop
panels.append((step3(OR, ORD, PU, PUD), ["3. Right cord: OVER the tail,", "BEHIND the core, UP through loop."]))
# P4: pulled snug - cords have swapped sides
p = (core() + knot_block(46)
     + cord("M64 52 Q50 70 50 100 L50 230", PU, PUD) + cord("M136 52 Q150 70 150 100 L150 230", OR, ORD))
panels.append((p, ["4. Pull both cords snug.", "That is one knot."]))
# P5: second knot = step 3 mirrored, hanging below knot 1
p = (f'<g transform="translate(200,26) scale(-1,0.88)">' + step3(OR, ORD, PU, PUD) + '</g>' + knot_block(46))
panels.append((p, ["5. Next knot: start on the", "RIGHT side. Same moves, mirrored."]))
# P6: many knots
p = core(16, 236) + "".join(knot_block(30 + 20*i) for i in range(10))
panels.append((p, ["6. Keep switching sides.", "Knots stack into a flat bar."]))

PW, PH = 226, 300
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="680" height="{2*PH+20}" viewBox="0 0 680 {2*PH+20}"><rect width="680" height="{2*PH+20}" fill="#fff"/>']
for i, (body, cap) in enumerate(panels):
    x, y = (i % 3)*PW + 7, (i // 3)*PH + 6
    svg.append(f'<g transform="translate({x+6},{y})"><rect x="-4" y="4" width="{PW-14}" height="{PH-8}" rx="10" fill="#fafaf8" stroke="#ddd"/>'
               f'<g transform="translate({(PW-14)/2-100-4},6)">{body}</g>')
    for j, c in enumerate(cap):
        svg.append(f'<text x="{(PW-14)/2-4:.0f}" y="{256+j*17}" {FONT} font-size="12.5" fill="#222" text-anchor="middle">{c}</text>')
    svg.append('</g>')
svg.append('</svg>')
open(f"{OUT}/cobra_knot_steps.svg", "w").write("\n".join(svg))
print("ok")

# ---------------- 3) quick-pull (quick-deploy) outer layer --------------------------
def bight(x1, x2, y, c, cd, gap=12):
    """a loop of cord (two legs + rounded tip) lying across the front, tip at x2"""
    d = 1 if x2 > x1 else -1
    return cord(f"M{x1} {y-gap/2} L{x2-d*gap/2} {y-gap/2} A{gap/2} {gap/2} 0 0 {1 if d>0 else 0} {x2-d*gap/2} {y+gap/2} L{x1} {y+gap/2}", c, cd)

panels = []
# Q1: loop instead of end
p = core() + cord("M140 30 L140 70", PU, PUD) + bight(140, 64, 82, PU, PUD) + cord("M140 94 L140 230", PU, PUD) + cord("M60 30 L60 230", OR, ORD)
panels.append((p, ["1. Fold cord into a loop.", "Use the loop, not the end."]))
# Q2: chain - each loop goes through the one before
p = core()
for i in range(7):
    y = 40 + i*26
    if i % 2 == 0:
        p += cord(f"M140 {y-14} L140 {y-6}", PU, PUD) + bight(140, 62, y, PU, PUD)
    else:
        p += cord(f"M60 {y-14} L60 {y-6}", OR, ORD) + bight(60, 138, y, OR, ORD)
panels.append((p, ["2. Each loop goes through", "the last one. Switch sides."]))
# Q3: lock the last loop
p = core()
for i in range(5):
    y = 40 + i*26
    p += (cord(f"M140 {y-14} L140 {y-6}", PU, PUD) + bight(140, 62, y, PU, PUD)) if i % 2 == 0 else (cord(f"M60 {y-14} L60 {y-6}", OR, ORD) + bight(60, 138, y, OR, ORD))
p += cord("M60 160 L60 200 Q60 214 76 214 L120 214", OR, ORD) + cord("M140 160 L140 196", PU, PUD)
p += '<circle cx="128" cy="210" r="11" fill="none" stroke="#d11" stroke-width="2.5" stroke-dasharray="4 3"/>'
panels.append((p, ["3. Push the end through", "the last loop and tuck it."]))
# Q4: pull to release
p = core() + cord("M60 30 L60 230", OR, ORD) + cord("M140 30 L140 230", PU, PUD)
p += ('<path d="M40 130 L14 130" stroke="#333" stroke-width="2.5" marker-end="url(#q)"/>'
      '<path d="M160 130 L186 130" stroke="#333" stroke-width="2.5" marker-end="url(#q)"/>')
panels.append((p, ["4. Untuck it and pull the", "sides apart. It unzips."]))

PW, PH = 170, 300
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="680" height="{PH+10}" viewBox="0 0 680 {PH+10}"><rect width="680" height="{PH+10}" fill="#fff"/>'
       '<defs><marker id="q" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 1L9 5L0 9z" fill="#333"/></marker></defs>']
for i, (body, cap) in enumerate(panels):
    x = i*PW + 2
    svg.append(f'<g transform="translate({x},2)"><rect x="2" y="4" width="{PW-6}" height="{PH-6}" rx="10" fill="#fafaf8" stroke="#ddd"/>'
               f'<g transform="translate({(PW-2)/2-100*0.75:.1f},10) scale(0.75)">{body}</g>')
    for j, c in enumerate(cap):
        svg.append(f'<text x="{(PW-2)/2:.0f}" y="{232+j*16}" {FONT} font-size="11" fill="#222" text-anchor="middle">{c}</text>')
    svg.append('</g>')
svg.append('</svg>')
open(f"{OUT}/quick_pull_steps.svg", "w").write("\n".join(svg))
print("quick ok")
