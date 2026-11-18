"""
Parametric model: Polaris 2883837 (bar PN 1824838) 7" High Rise ProTaper bar, AXYS RMK.
Units: mm.  Axes: X = left/right, Y = toward rider (+), Z = up.
Origin = center of the clamp area, on the bar centerline.

Every value marked EST is an estimate from photos. Replace it with a measured value
and run:  python3 rmk_bar.py   ->  writes rmk_bar_2883837.step
"""
import math
import cadquery as cq
from cadquery import Vector as V

P = dict(
    # --- main bar ---
    bar_od=22.2,          # 7/8" grip/clamp OD (ProTaper SE family is 7/8")
    clamp_half=56.0,      # EST: half-length of flat clamp area (re-proportioned from photo + 8" handle span)
    bottom_r=30.0,        # EST: bend radius, clamp area to riser
    rise=178.0,           # 7" rise, clamp CL to grip CL (published "7 in")
    riser_top_x=150.0,    # EST: X of riser/upper-bend intersection (sets riser lean)
    upper_r=55.0,         # EST: bend radius, riser to grip section
    grip_end_x=395.0,     # EST: half overall bar width (~32" overall)
    backsweep=35.0,       # EST: Y offset of bar end vs clamp area (toward rider)
    upsweep=12.0,         # EST: Z rise of bar end above the upper-bend vertex
    # --- grips / hooks ---
    grip_od=32.0, grip_len=140.0,   # EST
    hook_drop=65.0, hook_r=18.0,    # EST: bar-end hook, drops down
    # --- cross brace ---
    brace_z=110.0,        # EST: brace CL height above clamp CL
    brace_od=15.0,        # EST
    collar_od=34.0, collar_len=26.0,  # EST: forged clamp on riser
    # --- grab bar (arch) ---
    pivot_inset=8.0,      # EST: pivot inboard of collar centre
    pivot_y=-20.0,        # EST: pivot boss offset fore/aft (− = forward)
    pivot_od=20.0, pivot_len=14.0,
    arch_rise=115.0,      # EST: arch top above brace CL
    arch_tilt_deg=15.0,   # EST: arch leans toward rider
    arch_od=16.0, arch_pad_od=30.0,
)


def bent_path(pts, radii):
    """Polyline with tangent arcs at interior vertices -> cq.Wire (G1)."""
    pts = [V(*p) for p in pts]
    edges, start = [], pts[0]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        r = radii[i - 1]
        u1, u2 = (a - b).normalized(), (c - b).normalized()
        theta = math.acos(max(-1, min(1, u1.dot(u2))))
        t = r / math.tan(theta / 2)
        p1, p2 = b + u1 * t, b + u2 * t
        bis = (u1 + u2).normalized()
        mid = b + bis * (r / math.sin(theta / 2) - r)
        if (p1 - start).Length > 1e-6:
            edges.append(cq.Edge.makeLine(start, p1))
        edges.append(cq.Edge.makeThreePointArc(p1, mid, p2))
        start = p2
    edges.append(cq.Edge.makeLine(start, pts[-1]))
    return cq.Wire.assembleEdges(edges)


def tube(path, od):
    e0 = path.Edges()[0]
    p0, t0 = e0.startPoint(), e0.tangentAt(0)
    prof = cq.Wire.makeCircle(od / 2, p0, t0)
    return cq.Solid.sweep(prof, [], path, transitionMode="round")


def cyl(od, length, center, axis):
    axis = V(*axis).normalized()
    base = V(*center) - axis * (length / 2)
    return cq.Solid.makeCylinder(od / 2, length, base, axis)


p = P
# ---------- main bar ----------
right = [
    (p["clamp_half"] + 0.0, 0, 0),
    (p["riser_top_x"], 0, p["rise"]),
    (p["grip_end_x"], p["backsweep"], p["rise"] + p["upsweep"]),
]
# bottom-corner vertex sits where the clamp line meets the riser line
bx = p["clamp_half"] + p["bottom_r"]  # first bend vertex
right[0] = (bx, 0, 0)
pts = [(-x, y, z) for (x, y, z) in reversed(right)] + [(0, 0, 0)] + right
pts = [q for q in pts if True]
radii = [p["upper_r"], p["bottom_r"], 1e-3, p["bottom_r"], p["upper_r"]]
# remove the centre point (straight run) — handle by dropping it
pts.pop(3); radii = [p["upper_r"], p["bottom_r"], p["bottom_r"], p["upper_r"]]
bar = tube(bent_path(pts, radii), p["bar_od"])

parts = {"handlebar_1824838": (bar, cq.Color(0.45, 0.45, 0.47))}

# ---------- grips + hooks ----------
end = V(*right[2]); prev = V(*right[1])
gdir = (end - prev).normalized()
for side in (1, -1):
    m = V(side, 1, 1)
    e = V(end.x * side, end.y, end.z)
    d = V(gdir.x * side, gdir.y, gdir.z)
    grip = cyl(p["grip_od"], p["grip_len"], e - d * (p["grip_len"] / 2), d)
    hpath = bent_path(
        [e - d * 25, e + d * p["hook_r"], e + d * p["hook_r"] + V(0, 6, -p["hook_drop"])],
        [p["hook_r"]],
    )
    hook = tube(hpath, p["bar_od"])
    tag = "R" if side > 0 else "L"
    parts[f"grip_{tag}"] = (grip, cq.Color(0.08, 0.08, 0.08))
    parts[f"hook_{tag}"] = (hook, cq.Color(0.08, 0.08, 0.08))

# ---------- brace + collars ----------
# riser line: from bottom vertex to riser-top vertex
b0, b1 = V(bx, 0, 0), V(*right[1])
s = p["brace_z"] / b1.z
riser_pt = b0 + (b1 - b0) * s
rdir = (b1 - b0).normalized()
cx = riser_pt.x
collars = []
for side in (1, -1):
    c = V(cx * side, 0, p["brace_z"])
    ax = V(rdir.x * side, rdir.y, rdir.z)
    col = cyl(p["collar_od"], p["collar_len"], c, ax)
    hole = cyl(p["bar_od"], p["collar_len"] + 2, c, ax)
    parts[f"brace_clamp_{'R' if side>0 else 'L'}"] = (col.cut(hole), cq.Color(0.1, 0.1, 0.1))
brace_len = 2 * cx - p["bar_od"]
brace = cyl(p["brace_od"], brace_len, (0, 0, p["brace_z"]), (1, 0, 0))
parts["cross_brace"] = (brace, cq.Color(0.45, 0.45, 0.47))

# ---------- grab bar (arch) + pivots ----------
px = cx - p["pivot_inset"]
tilt = math.radians(p["arch_tilt_deg"])
up = V(0, math.sin(tilt), math.cos(tilt))
pl, pr = V(-px, p["pivot_y"], p["brace_z"]), V(px, p["pivot_y"], p["brace_z"])
top = V(0, p["pivot_y"], p["brace_z"]) + up * p["arch_rise"]
arch_path = cq.Wire.assembleEdges([cq.Edge.makeThreePointArc(pl, top, pr)])
arch = tube(arch_path, p["arch_od"])
pad = tube(arch_path, p["arch_pad_od"]).cut(arch)
for side in (1, -1):
    pv = cyl(p["pivot_od"], p["pivot_len"], (px * side, p["pivot_y"] / 2, p["brace_z"]), (0, 1, 0))
    parts[f"grab_pivot_{'R' if side>0 else 'L'}"] = (pv, cq.Color(0.1, 0.1, 0.1))
parts["grab_bar_tube"] = (arch, cq.Color(0.3, 0.3, 0.3))
parts["grab_bar_pad"] = (pad, cq.Color(0.05, 0.05, 0.05))

# ---------- export ----------
asm = cq.Assembly(name="RMK_7in_HighRise_2883837")
for name, (solid, col) in parts.items():
    assert solid.isValid(), name
    asm.add(cq.Workplane().add(solid), name=name, color=col)
asm.save("rmk_bar_2883837.step")
print("bar width overall: %.0f mm (%.1f in)" % (2 * (p["grip_end_x"] + p["hook_r"]), 2 * (p["grip_end_x"] + p["hook_r"]) / 25.4))
print("brace collar CL x = ±%.1f mm, brace span %.1f mm" % (cx, brace_len))
print("ok:", list(parts))
