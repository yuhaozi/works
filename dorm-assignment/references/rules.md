# Dorm Assignment Rules

## Building Pools

Female dormitories:
- 林曦楼A栋、林曦楼B栋
- 秀逸楼A栋、秀逸楼B栋
- 钟萃楼A栋、钟萃楼B栋
- 灵韵楼A栋、灵韵楼B栋
- 杏雨楼A栋、杏雨楼B栋

Male dormitories:
- 春晖楼A栋、春晖楼B栋
- 暖煦楼
- 毓慧楼A栋、毓慧楼B栋

`暖煦楼` has no A/B block. All other named buildings have A/B blocks.

Use `building_id = 楼名 + 栋号` as the hard boundary. `林曦楼A栋` and `林曦楼B栋` are different building IDs.

## Capacity and Department Rules

- Standard room capacity: 6 people.
- Small department threshold: count < 200.
- Mixed room maximum: 2 departments.
- Teacher-facing output: department, gender, building ID, independent room numbers, mixed room numbers and composition.

## Floor Preferences

- Preferred middle floors: 3 and 4.
- All floors may be used if the user says so.
- Remainder stitching priority: same building ID + same floor, then same building ID + adjacent floor.
- Do not stitch a department remainder across building IDs.

## Orientation Rules

If room orientation is not supplied, derive it from the last two digits of the room number.

Default buildings:
- shady side: odd suffixes 01-23
- sunny side: even suffixes 02-36

毓慧楼:
- shady side: odd suffixes 01-15
- sunny side: even suffixes 02-28

秀逸楼A栋:
- shady side: odd suffixes 01-19
- sunny side: even suffixes 02-32

If a suffix is outside the known range, mark orientation as `unknown` and keep the room usable unless the user says otherwise.

## Opposite-Door Parameter

Prefer explicit `opposite_room_id` from the room table. Use a stable room ID format:

```text
building_id-floor-room
林曦楼A栋-3-301
```

Rules:
- Opposite-door assignment is a soft constraint.
- Within the same building and floor, assign opposite-door pairs to the same department when possible.
- Do not let opposite-door preference override gender separation, capacity, building boundary, or mixed-room maximum.
- If the provided opposite-door mapping is one-way, warn the user and either mirror it or treat it as advisory.

Suggested soft-constraint order:

```text
same building ID > same floor > opposite-door pair > contiguous room numbers > adjacent room numbers > adjacent floor
```

## Input Schemas

Department table:

```csv
department,gender,count
计算机学院,男,310
计算机学院,女,176
```

Room table:

```csv
gender,building,block,building_id,floor,room,capacity,opposite_room_id
女,林曦楼,A,林曦楼A栋,3,301,6,林曦楼A栋-3-302
女,林曦楼,A,林曦楼A栋,3,302,6,林曦楼A栋-3-301
男,暖煦楼,,暖煦楼,4,401,6,暖煦楼-4-402
```

Optional override table:

```csv
department,priority,compact_required,preferred_building_id,forbidden_building_ids
外国语学院,high,true,秀逸楼A栋,
```

## Validation Checklist

- Gender-specific assignments use only the correct gender room pool.
- Assigned room capacity is not exceeded.
- Every department/gender count matches final assigned people.
- A room is not assigned to two unrelated full-room blocks.
- Mixed rooms contain no more than two departments.
- Each department remainder stays in one of its own assigned building IDs.
- Remainder rooms are same floor or adjacent floor to that department's main block in the same building ID.
- Opposite-door pairs are used where possible and skipped only for stronger constraints.
