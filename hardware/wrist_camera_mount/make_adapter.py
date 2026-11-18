"""Adapter: OV9281 USB board (~38x38, holes PITCH mm apart) -> official SO-101 wrist camera mount.

The official mount (assets/so101_meshes/wrist_camera_mount_so101_v1.stl, the SO-101 hex-nut wrist mount)
holds a 32x32 board on 4x M2 holes in a 27 x 27 mm square (measured from the STL); the lens looks
THROUGH the 16 x 25 mm window in the plate, towards the jaws. A 38x38 board does not fit, so this plate
goes between them: countersunk M2 screws fix it to the mount, the board lies flat on it (lens down,
through both windows) and is screwed into the 4 outer holes.

Run:  python make_adapter.py [PITCH_MM]      (default 34; MEASURE your board: hole centre to centre)
Needs: trimesh + manifold3d (pip). Writes the STL next to this file.
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).parent
MOUNT = HERE.parents[1] / "assets/so101_meshes/wrist_camera_mount_so101_v1.stl"

PITCH = float(sys.argv[1]) if len(sys.argv) > 1 else 34.0  # board hole pitch — measure it!
BOARD = PITCH + 4.0          # board edge (38 for pitch 34)
MOUNT_PITCH = 27.0           # official mount hole square (measured)
T = 3.0                      # plate thickness
PILOT_D = 1.8                # M2 self-tapping into PLA/PETG (board screws)
CLEAR_D = 2.3                # M2 clearance (mount screws)
CSK_D = 4.2                  # M2 countersunk head, flush so the board lies flat on it
WINDOW = (18.0, 25.0)        # lens opening (u, z); official plate window is 16 x 25

# Measured on the official STL: outward normal of the camera plate's back face, its offset, hole-square centre.
N = np.array([-0.4226, -0.9063, 0.0]); N /= np.linalg.norm(N)
U = np.array([-N[1], N[0], 0.0])
Z = np.array([0.0, 0.0, 1.0])
FACE, CU, CZ = 55.40, -28.62, 17.5

if PITCH < 33:
    sys.exit(f"pitch {PITCH} mm: board is ~32x32 — print the official mount as is, no adapter needed")


def cyl(d, h, x, y, z0):
    c = trimesh.creation.cylinder(radius=d / 2, height=h, sections=48)
    c.apply_translation([x, y, z0 + h / 2])
    return c


def build():
    # plate frame: z=0 lies on the mount's back face, +z away from the gripper (board side)
    plate = trimesh.creation.box([BOARD, BOARD, T])
    plate.apply_translation([0, 0, T / 2])
    cuts = [trimesh.creation.box([WINDOW[0], WINDOW[1], 3 * T])]
    h, p = MOUNT_PITCH / 2, PITCH / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(CLEAR_D, 3 * T, sx * h, sy * h, -T))
            cone = trimesh.creation.cone(radius=CSK_D / 2, height=CSK_D / 2, sections=48)
            cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
            cone.apply_translation([sx * h, sy * h, T + 0.01])  # 90° countersink on the board side
            cuts.append(cone)
            cuts.append(cyl(PILOT_D, 3 * T, sx * p, sy * p, -T))
    return plate.difference(trimesh.boolean.union(cuts))


def plate_to_mount():
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = U, Z, N, N * FACE + U * CU + Z * CZ
    return M


def place_on_mount(part):
    return part.copy().apply_transform(plate_to_mount())


def check(adapter, mount):
    assert adapter.is_watertight, "adapter mesh not closed"
    placed = place_on_mount(adapter)
    clash = placed.intersection(mount)
    assert clash.is_empty or clash.volume < 0.5, f"adapter overlaps mount: {clash.volume:.2f} mm3"
    for cu in (CU - 13.5, CU + 13.5):
        for cz in (CZ - 13.5, CZ + 13.5):
            p = N * 70 + U * cu + Z * cz
            assert not placed.ray.intersects_any([p], [-N])[0], f"adapter blocks screw at u={cu} z={cz}"
            locs, _, _ = mount.ray.intersects_location([p], [-N])
            first = min(np.linalg.norm(locs - p, axis=1), default=1e9)
            assert first > 70 - 51.2 + 0.5, f"mount hole not where expected at u={cu} z={cz}"
            beside = p + Z * (3.0 if cz < CZ else -3.0)  # 3 mm inward: plate must be there, seated on the face
            hit, _, _ = placed.ray.intersects_location([beside], [-N])
            assert len(hit) and abs(min(np.linalg.norm(hit - beside, axis=1)) - (70 - FACE - T)) < 0.05, "not seated"
    # lens path: straight through adapter window and mount window
    c = N * 70 + U * CU + Z * CZ
    for du, dz in ((0, 0), (7.0, 0), (-7.0, 0), (0, 12.0), (0, -12.0)):  # window has rounded corners
        q = c + U * du + Z * dz
        assert not placed.ray.intersects_any([q], [-N])[0], "adapter window too small"
        assert not mount.ray.intersects_any([q], [-N])[0], "mount window blocked"
    return placed


if __name__ == "__main__":
    mount = trimesh.load(MOUNT)
    adapter = build()
    check(adapter, mount)
    out = HERE / f"ov9281_adapter_{BOARD:.0f}mm_pitch{PITCH:g}.stl"
    adapter.export(out)
    print(f"OK {out.name}: {adapter.extents.round(1)} mm, {adapter.volume / 1000:.2f} cm3, seated, holes + lens path clear")
