#!/usr/bin/env python3
"""Baseline dorm allocator for department-level assignments.

Inputs:
  departments.csv: department,gender,count
  rooms.csv: gender,building,block,building_id,floor,room,capacity,opposite_room_id

Outputs:
  assignments.csv
  mixed_rooms.csv
  validation.csv

This script favors deterministic, inspectable behavior over global optimality.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


CAPACITY = 6
SMALL_DEPT_THRESHOLD = 200


@dataclass(frozen=True)
class Dept:
    department: str
    gender: str
    count: int


@dataclass
class Room:
    gender: str
    building: str
    block: str
    building_id: str
    floor: int
    room: str
    capacity: int
    opposite_room_id: str
    room_id: str
    orientation: str


def suffix(room: str) -> int | None:
    digits = "".join(ch for ch in str(room) if ch.isdigit())
    if len(digits) < 2:
        return None
    return int(digits[-2:])


def infer_orientation(building_id: str, room: str) -> str:
    n = suffix(room)
    if n is None:
        return "unknown"
    if "毓慧楼" in building_id:
        if n % 2 == 1 and 1 <= n <= 15:
            return "shady"
        if n % 2 == 0 and 2 <= n <= 28:
            return "sunny"
    elif building_id == "秀逸楼A栋":
        if n % 2 == 1 and 1 <= n <= 19:
            return "shady"
        if n % 2 == 0 and 2 <= n <= 32:
            return "sunny"
    else:
        if n % 2 == 1 and 1 <= n <= 23:
            return "shady"
        if n % 2 == 0 and 2 <= n <= 36:
            return "sunny"
    return "unknown"


def room_sort_key(room: Room) -> tuple:
    middle_rank = 0 if room.floor in (3, 4) else abs(room.floor - 3.5)
    orientation_rank = {"sunny": 0, "shady": 1, "unknown": 2}[room.orientation]
    return (middle_rank, orientation_rank, room.building_id, room.floor, suffix(room.room) or 999, room.room)


def read_departments(path: Path) -> list[Dept]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [
            Dept(row["department"].strip(), row["gender"].strip(), int(row["count"]))
            for row in csv.DictReader(f)
            if row.get("department")
        ]


def read_rooms(path: Path) -> list[Room]:
    rooms = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            building_id = row.get("building_id", "").strip()
            floor = int(row["floor"])
            room = str(row["room"]).strip()
            room_id = f"{building_id}-{floor}-{room}"
            rooms.append(
                Room(
                    gender=row["gender"].strip(),
                    building=row.get("building", "").strip(),
                    block=row.get("block", "").strip(),
                    building_id=building_id,
                    floor=floor,
                    room=room,
                    capacity=int(row.get("capacity") or CAPACITY),
                    opposite_room_id=row.get("opposite_room_id", "").strip(),
                    room_id=room_id,
                    orientation=row.get("orientation", "").strip() or infer_orientation(building_id, room),
                )
            )
    return rooms


def choose_room_block(available: list[Room], needed: int) -> list[Room]:
    if needed <= 0:
        return []

    by_building = defaultdict(list)
    for room in available:
        by_building[room.building_id].append(room)

    # Prefer one building with enough capacity; within it, deterministic scored rooms.
    candidates = [rooms for rooms in by_building.values() if len(rooms) >= needed]
    if candidates:
        candidates.sort(key=lambda xs: (min(room_sort_key(r) for r in xs), len(xs)))
        return sorted(candidates[0], key=room_sort_key)[:needed]

    return sorted(available, key=room_sort_key)[:needed]


def allocate_gender(depts: list[Dept], rooms: list[Room]) -> tuple[list[dict], list[dict], list[dict]]:
    available = sorted(rooms, key=room_sort_key)
    assigned_ids = set()
    full_rows = []
    remainders = []

    # Large departments first, then small departments for compact zones.
    ordered = sorted(depts, key=lambda d: (d.count < SMALL_DEPT_THRESHOLD, -d.count, d.department))

    for dept in ordered:
        full_count, remainder = divmod(dept.count, CAPACITY)
        free_rooms = [r for r in available if r.room_id not in assigned_ids]
        picked = choose_room_block(free_rooms, full_count)
        for room in picked:
            assigned_ids.add(room.room_id)
            full_rows.append(
                {
                    "department": dept.department,
                    "gender": dept.gender,
                    "building_id": room.building_id,
                    "floor": room.floor,
                    "room": room.room,
                    "room_id": room.room_id,
                    "people": CAPACITY,
                    "mixed": "false",
                }
            )
        if remainder:
            seed_rooms = picked
            if not seed_rooms:
                # A department with fewer than 6 people has no full-room block.
                # Give it an advisory compact-zone anchor so it can be stitched
                # with another remainder without inventing a cross-building move.
                seed_rooms = choose_room_block([r for r in available if r.room_id not in assigned_ids], 1)
            main_buildings = [r.building_id for r in picked] or []
            main_floors = [r.floor for r in picked] or []
            main_buildings = [r.building_id for r in seed_rooms] or []
            main_floors = [r.floor for r in seed_rooms] or []
            remainders.append(
                {
                    "department": dept.department,
                    "gender": dept.gender,
                    "remainder": remainder,
                    "main_buildings": main_buildings,
                    "main_floors": main_floors,
                }
            )

    mixed_rows = stitch_remainders(remainders, available, assigned_ids)
    validation = validate(depts, full_rows, mixed_rows)
    return full_rows, mixed_rows, validation


def compatible(a: dict, b: dict) -> bool:
    if a["department"] == b["department"]:
        return False
    if a["gender"] != b["gender"]:
        return False
    if a["remainder"] + b["remainder"] != CAPACITY:
        return False
    shared_buildings = set(a["main_buildings"]) & set(b["main_buildings"])
    if not shared_buildings:
        return False
    floors_a = set(a["main_floors"])
    floors_b = set(b["main_floors"])
    return any(abs(x - y) <= 1 for x in floors_a for y in floors_b)


def stitch_remainders(remainders: list[dict], rooms: list[Room], assigned_ids: set[str]) -> list[dict]:
    mixed_rows = []
    used_remainders = set()
    free = [r for r in rooms if r.room_id not in assigned_ids]

    for i, a in enumerate(remainders):
        if i in used_remainders:
            continue
        partner_idx = None
        for j, b in enumerate(remainders):
            if j <= i or j in used_remainders:
                continue
            if compatible(a, b):
                partner_idx = j
                break
        if partner_idx is None:
            mixed_rows.append({**a, "status": "unresolved", "room_id": "", "building_id": "", "floor": "", "room": ""})
            continue

        b = remainders[partner_idx]
        buildings = list(set(a["main_buildings"]) & set(b["main_buildings"]))
        target_building = buildings[0]
        target_floors = sorted(set(a["main_floors"]) | set(b["main_floors"]))
        candidates = [
            r
            for r in free
            if r.building_id == target_building and any(abs(r.floor - f) <= 1 for f in target_floors)
        ]
        if not candidates:
            mixed_rows.append({**a, "status": "unresolved", "room_id": "", "building_id": "", "floor": "", "room": ""})
            continue
        room = sorted(candidates, key=room_sort_key)[0]
        free.remove(room)
        assigned_ids.add(room.room_id)
        used_remainders.update({i, partner_idx})
        for item in (a, b):
            mixed_rows.append(
                {
                    "department": item["department"],
                    "gender": item["gender"],
                    "building_id": room.building_id,
                    "floor": room.floor,
                    "room": room.room,
                    "room_id": room.room_id,
                    "people": item["remainder"],
                    "mixed_with": b["department"] if item is a else a["department"],
                    "status": "assigned",
                }
            )
    return mixed_rows


def validate(depts: list[Dept], full_rows: list[dict], mixed_rows: list[dict]) -> list[dict]:
    totals = defaultdict(int)
    for row in full_rows:
        totals[(row["department"], row["gender"])] += int(row["people"])
    for row in mixed_rows:
        if row.get("status") == "assigned":
            totals[(row["department"], row["gender"])] += int(row["people"])
    out = []
    for dept in depts:
        actual = totals[(dept.department, dept.gender)]
        out.append(
            {
                "department": dept.department,
                "gender": dept.gender,
                "expected": dept.count,
                "actual": actual,
                "ok": str(actual == dept.count).lower(),
            }
        )
    return out


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--departments", required=True, type=Path)
    parser.add_argument("--rooms", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    departments = read_departments(args.departments)
    rooms = read_rooms(args.rooms)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    all_full = []
    all_mixed = []
    all_validation = []
    for gender in sorted({d.gender for d in departments}):
        gender_depts = [d for d in departments if d.gender == gender]
        gender_rooms = [r for r in rooms if r.gender == gender]
        full, mixed, validation = allocate_gender(gender_depts, gender_rooms)
        all_full.extend(full)
        all_mixed.extend(mixed)
        all_validation.extend(validation)

    write_csv(
        args.out_dir / "assignments.csv",
        all_full,
        ["department", "gender", "building_id", "floor", "room", "room_id", "people", "mixed"],
    )
    write_csv(
        args.out_dir / "mixed_rooms.csv",
        all_mixed,
        ["department", "gender", "building_id", "floor", "room", "room_id", "people", "mixed_with", "status"],
    )
    write_csv(args.out_dir / "validation.csv", all_validation, ["department", "gender", "expected", "actual", "ok"])


if __name__ == "__main__":
    main()
