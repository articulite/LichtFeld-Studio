"""Create a deterministic, spatially blocked COLMAP screening split.

The source dataset is never modified. Images are hard-linked when possible;
COLMAP records are rewritten so held-out groups occur at ``test_every``
intervals, and point tracks are restricted to training cameras.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def read_images(path: Path):
    records = []
    with path.open("rb") as f:
        n, = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            start = f.tell()
            image_id, = struct.unpack("<i", f.read(4))
            q = struct.unpack("<4d", f.read(32)); t = struct.unpack("<3d", f.read(24))
            camera_id, = struct.unpack("<i", f.read(4))
            name = bytearray()
            while True:
                c = f.read(1)
                if not c: raise ValueError("truncated images.bin name record")
                if c == b"\0": break
                name.extend(c)
            count, = struct.unpack("<Q", f.read(8)); f.seek(count * 24, 1)
            end = f.tell(); f.seek(start); raw = f.read(end - start)
            w, x, y, z = q
            R = ((1-2*y*y-2*z*z, 2*x*y-2*z*w, 2*x*z+2*y*w),
                 (2*x*y+2*z*w, 1-2*x*x-2*z*z, 2*y*z-2*x*w),
                 (2*x*z-2*y*w, 2*y*z+2*x*w, 1-2*x*x-2*y*y))
            center = tuple(-sum(R[j][k] * t[j] for j in range(3)) for k in range(3))
            text = name.decode("utf-8", "replace")
            # The supplied cubemap dataset stores faces in numbered folders,
            # while the pipeline dataset encodes the capture in the filename.
            group = (Path(text).name if "/" in text or "\\" in text
                     else text.rsplit("_perspective_", 1)[0])
            records.append({"id": image_id, "name": text, "group": group, "center": center, "raw": raw, "camera_id": camera_id})
    return records


def write_points(src: Path, dst: Path, train_ids: set[int]) -> tuple[int, int]:
    kept = total = 0
    with src.open("rb") as f, dst.open("wb") as out:
        count, = struct.unpack("<Q", f.read(8)); payload = []
        for _ in range(count):
            point_id = f.read(8); xyz = f.read(24); rgb = f.read(3); error = f.read(8)
            n, = struct.unpack("<Q", f.read(8)); tracks = [f.read(8) for _ in range(n)]
            total += 1
            tracks = [x for x in tracks if struct.unpack("<i", x[:4])[0] in train_ids]
            if tracks:
                payload.append(point_id + xyz + rgb + error + struct.pack("<Q", len(tracks)) + b"".join(tracks)); kept += 1
        out.write(struct.pack("<Q", kept)); out.write(b"".join(payload))
    return total, kept


def link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try: dst.hardlink_to(src)
    except OSError: shutil.copy2(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--groups", type=int, default=0, help="0 selects up to 24 complete groups")
    ap.add_argument("--holdout-groups", type=int, default=0, help="0 selects one eighth of groups")
    ap.add_argument("--test-every", type=int, default=8, choices=[8], help="This screening adapter implements a 7:1 split")
    args = ap.parse_args()
    root, out = args.dataset.resolve(), args.output.resolve()
    sparse = root / "sparse" / "0"
    recs = read_images(sparse / "images.bin")
    groups: dict[str, list[dict]] = {}
    for r in recs: groups.setdefault(r["group"], []).append(r)
    face_counts = sorted({len(rs) for rs in groups.values()})
    if len(face_counts) != 1: raise SystemExit(f"groups have inconsistent face counts: {face_counts}")
    faces_per_group = face_counts[0]
    complete = [g for g, rs in groups.items() if len(rs) == faces_per_group]
    complete.sort()
    requested = args.groups or (24 if len(complete) >= 24 else 8)
    group_count = min(len(complete), requested)
    group_count -= group_count % 8
    holdout_count = args.holdout_groups or group_count // 8
    if holdout_count >= group_count: raise SystemExit("holdout must be smaller than selected groups")
    if group_count < 8: raise SystemExit("need at least eight complete groups for a 7:1 split")
    # Spread the development subset across the capture trajectory so the
    # held-out groups are not a contiguous neighborhood of the training set.
    indices = sorted({round(i * (len(complete) - 1) / (group_count - 1)) for i in range(group_count)})
    chosen = [complete[i] for i in indices]
    # Farthest-in-sequence deterministic holdouts, preserving a two-group guard.
    held: list[str] = []
    hold_indices = [round(i * (group_count - 1) / (holdout_count - 1)) for i in range(holdout_count)] if holdout_count > 1 else [group_count // 2]
    held = [chosen[i] for i in hold_indices]
    chosen_positions = {complete.index(g) for g in chosen}
    held_positions = {complete.index(g) for g in held}
    guard = [p for p in chosen_positions - held_positions if any(abs(p - h) < 2 for h in held_positions)]
    if guard:
        raise SystemExit(f"selected training groups violate one-capture sequence guard: {guard}")
    if len(held) != holdout_count: raise SystemExit("could not form guarded holdout groups")
    held_set = set(held); train_groups = [g for g in chosen if g not in held_set]
    train = [r for g in train_groups for r in groups[g]]; valid = [r for g in held for r in groups[g]]
    # Preserve group integrity while placing each validation face at test_every slots.
    ordered = []; ti = vi = 0
    while ti < len(train) or vi < len(valid):
        if vi < len(valid): ordered.append(valid[vi]); vi += 1
        for _ in range(args.test_every - 1):
            if ti < len(train): ordered.append(train[ti]); ti += 1
    held_ids = {r["id"] for r in valid}
    eval_slots = {i for i, r in enumerate(ordered) if i % args.test_every == 0}
    actual_eval = {i for i, r in enumerate(ordered) if r["id"] in held_ids}
    if eval_slots != actual_eval:
        raise SystemExit(f"split placement error: expected eval slots {len(eval_slots)}, actual {len(actual_eval)}")
    if out.exists(): raise SystemExit(f"output exists: {out}")
    if not out.is_absolute(): raise SystemExit("output must be absolute")
    if out == root or root in out.parents: raise SystemExit("output must not be inside source dataset")
    (out / "images").mkdir(parents=True); (out / "masks").mkdir(exist_ok=True); (out / "sparse" / "0").mkdir(parents=True)
    for r in ordered:
        if Path(r["name"]).is_absolute() or ".." in Path(r["name"]).parts:
            raise SystemExit(f"image name must be a contained relative path: {r['name']}")
        src = (root / "images" / r["name"]).resolve()
        if not src.is_relative_to((root / "images").resolve()): raise SystemExit(f"image escapes source images: {r['name']}")
        if not src.is_file(): raise SystemExit(f"missing image: {src}")
        link(src, out / "images" / r["name"])
        mask = (root / "masks" / Path(r["name"]).with_suffix(".png")).resolve()
        if root not in mask.parents: raise SystemExit(f"mask escapes source root: {r['name']}")
        if mask.is_file(): link(mask, out / "masks" / Path(r["name"]).with_suffix(".png"))
    link(sparse / "cameras.bin", out / "sparse" / "0" / "cameras.bin")
    with (out / "sparse" / "0" / "images.bin").open("wb") as f:
        f.write(struct.pack("<Q", len(ordered))); [f.write(r["raw"]) for r in ordered]
    total_points, kept_points = write_points(sparse / "points3D.bin", out / "sparse" / "0" / "points3D.bin", {r["id"] for r in train})
    held_source_indices = [complete.index(g) for g in held]
    centers = {g: tuple(sum(r["center"][j] for r in groups[g]) / len(groups[g]) for j in range(3)) for g in chosen}
    held_train_distances = {g: min(math.dist(centers[g], centers[t]) for t in train_groups) for g in held}
    if any(d <= 1e-9 for d in held_train_distances.values()): raise SystemExit("held-out and training capture centers coincide")
    excluded_neighbors = [g for g in complete if g not in chosen and any(abs(complete.index(g) - i) <= 1 for i in held_source_indices)]
    manifest = {"source": str(root), "source_images_sha256": digest(sparse / "images.bin"), "source_points_sha256": digest(sparse / "points3D.bin"), "groups": chosen, "train_groups": train_groups, "heldout_groups": held, "counts": {"groups": len(chosen), "train_groups": len(train_groups), "heldout_groups": len(held), "faces_per_group": faces_per_group, "train_faces": len(train), "heldout_faces": len(valid), "points_total": total_points, "points_kept": kept_points}, "test_every": args.test_every, "record_order": "heldout records at modulo-0 positions, followed by test_every-1 training records; source record bytes preserved", "evaluation_indices_modulo": 0, "excluded_neighbor_groups": excluded_neighbors, "held_train_center_min_distance": held_train_distances, "spatial_guard": "selected groups are spread over source sequence; selected training groups are not immediate neighbors of held-out groups"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
