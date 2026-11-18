"""
TPU arch core for paracord grab handle - Polaris RMK ProTaper bar.
Units mm. Arch lies flat in XY (print orientation), Z up from bed.
Arch centre line: half circle, 8 in span x 4 in height, centred on the
anchor points (loop centres on the cross brace).
"""
import math
import cadquery as cq

SPAN = 8 * 25.4          # loop centre to loop centre
RISE = 4 * 25.4          # brace CL to arch-top CL
CORE_D = 14.0            # core OD
GROOVE_D = 4.4           # 550 cord is ~3.8-4.0 mm; one leg per groove
GROOVE_DEPTH = 2.6       # how far groove sinks into core
END_GAP = 20.0           # core stops this far above brace CL (room for loops)
FLAT = 0.8               # bed flat depth (no supports needed)

R = SPAN / 2             # half circle: RISE == R when span = 2 x rise
assert abs(R - RISE) < 0.01
a0 = math.asin(END_GAP / R)
a1 = math.pi - a0

def pt(a, r=R):
    return cq.Vector(r * math.cos(a), r * math.sin(a), 0)

path = cq.Wire.assembleEdges([cq.Edge.makeThreePointArc(pt(a0), pt(math.pi / 2), pt(a1))])
start = pt(a0)
tangent = cq.Vector(-math.sin(a0), math.cos(a0), 0)
radial = cq.Vector(math.cos(a0), math.sin(a0), 0)
plane = cq.Plane(origin=start, xDir=radial, normal=tangent)

core = cq.Workplane(plane).circle(CORE_D / 2).sweep(cq.Workplane().add(path))

# four grooves at 45/135/225/315 deg -> clear of the bed flat at 270
gc = CORE_D / 2 + GROOVE_D / 2 - GROOVE_DEPTH
for ang in (45, 135, 225, 315):
    t = math.radians(ang)
    g = (cq.Workplane(plane).center(gc * math.cos(t), gc * math.sin(t))
         .circle(GROOVE_D / 2).sweep(cq.Workplane().add(path)))
    core = core.cut(g)

# bed flat
core = core.cut(cq.Workplane().box(600, 600, 20).translate((0, 0, -CORE_D / 2 + FLAT - 10)))
# move so the bed is Z=0
core = core.translate((0, 0, CORE_D / 2 - FLAT))

solid = core.val()
assert solid.isValid()
bb = solid.BoundingBox()
cq.exporters.export(core, "tpu_arch_core.step")
cq.exporters.export(core, "tpu_arch_core.stl", tolerance=0.05, angularTolerance=0.1)
print("arc length CL: %.0f mm (%.1f in)" % (R * (a1 - a0), R * (a1 - a0) / 25.4))
print("footprint: %.0f x %.0f x %.1f mm" % (bb.xlen, bb.ylen, bb.zlen))
print("volume: %.1f cm3" % (solid.Volume() / 1000))
