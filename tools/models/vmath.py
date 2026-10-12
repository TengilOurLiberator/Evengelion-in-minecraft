"""Small vector / rotation maths for the model authoring library (numpy, right-handed rotations, rig space: +x left, +y up, +z forward)."""
import math

import numpy as np

I3 = np.eye(3)


def rax(axis, deg):
    """Right-handed rotation matrix about a unit axis ('x', 'y', 'z' or a 3-vector)."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if isinstance(axis, str):
        if axis == "x":
            return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)
        if axis == "y":
            return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)
        if axis == "z":
            return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)
        raise ValueError(axis)
    x, y, z = np.asarray(axis, float) / np.linalg.norm(axis)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]], float)


def chain(*mats):
    """chain(A, B, C) = A @ B @ C : C is applied to a vector first."""
    out = np.eye(3)
    for m in mats:
        out = out @ m
    return out


def euler_zyx(R):
    """Angles (x, y, z) in degrees with R = Rz(z) @ Ry(y) @ Rx(x): what 26.3's `rotation: {x, y, z}` means (verified with JOML rotationZYX)."""
    sy = -R[2, 0]
    y = math.asin(max(-1.0, min(1.0, sy)))
    if abs(sy) < 0.999999:
        x = math.atan2(R[2, 1], R[2, 2])
        z = math.atan2(R[1, 0], R[0, 0])
    else:
        x = math.atan2(-R[1, 2], R[1, 1])
        z = 0.0
    return math.degrees(x), math.degrees(y), math.degrees(z)


def from_euler_zyx(x, y, z):
    return chain(rax("z", z), rax("y", y), rax("x", x))


def quat_from_mat(R):
    """(x, y, z, w) of a rotation matrix."""
    t = R[0, 0] + R[1, 1] + R[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return ((R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, 0.25 * s)
    if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        return (0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s, (R[2, 1] - R[1, 2]) / s)
    if R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        return ((R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s, (R[0, 2] - R[2, 0]) / s)
    s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
    return ((R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s, (R[1, 0] - R[0, 1]) / s)


def mat_from_quat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]], float)


def mirror_x_mat(R):
    """The rotation R seen in a mirrored (x -> -x) frame."""
    M = np.diag([-1.0, 1.0, 1.0])
    return M @ R @ M


def look_matrix(eye, target, up=(0, 1, 0)):
    """Rows = camera right, up, forward expressed in world coordinates (a right-handed camera looking along its +forward)."""
    eye, target = np.asarray(eye, float), np.asarray(target, float)
    f = target - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, np.asarray(up, float))
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return np.stack([r, u, f])
