---
name: dorm-assignment
description: Generate and validate dormitory assignment plans from department headcount and room inventory data. Use when Codex needs to allocate students to dorm rooms by department, gender, building, floor, room orientation, small-department clustering, opposite-door preference, remainder stitching, or produce per-department Word/Excel reports for teachers.
---

# Dorm Assignment

## Overview

Use this skill to produce dormitory allocation plans where the output is department-level room assignments, not individual bed assignments.

Default domain assumptions for the current project:
- Room capacity is 6.
- Male and female students are modeled separately.
- Small departments have fewer than 200 students and should be placed compactly.
- Middle floors 3-4 and sunny/even rooms are preferred.
- Mixed rooms may contain at most two departments.
- Department remainders must not cross building IDs and should be on the same floor or adjacent floors.
- Opposite-door rooms should be assigned to the same department when possible.

Read `references/rules.md` before designing an allocation or editing the algorithm.

## Workflow

1. Collect inputs.
   - Department table: `department,gender,count`.
   - Room table: `gender,building,block,building_id,floor,room,capacity,opposite_room_id`.
   - Optional override table: department priority, fixed building, forbidden building, compact-zone hints.

2. Normalize rooms.
   - Treat `building_id` as the hard building boundary. For A/B buildings, use values such as `林曦楼A栋`; for `暖煦楼`, use `暖煦楼`.
   - If `opposite_room_id` is provided, prefer it over inferred opposite-door logic.
   - Derive orientation from the room-number suffix using `references/rules.md` unless the room table already supplies a verified orientation field.

3. Build separate models by gender.
   - Never mix genders in a model, a room pool, or a report.

4. Allocate whole-room blocks first.
   - Large departments: prefer compact contiguous blocks.
   - Small departments: prefer compact co-located zones.
   - Score rooms by middle floor, sunny side, same building, same floor, opposite-door pairing, contiguous or adjacent rooms.

5. Stitch remainders.
   - Combine remainders only within the same gender and same `building_id`.
   - Prefer same-floor pairings; allow adjacent floors if necessary.
   - Limit mixed rooms to two departments.
   - If a valid pair cannot be found, report it as unresolved instead of silently breaking hard constraints.

6. Validate and report.
   - For each department/gender, verify `independent_rooms * 6 + own_mixed_count == count`.
   - Verify no room is assigned twice.
   - Verify every mixed room has at most two departments.
   - Verify remainder rooms do not cross `building_id`.
   - Produce a global report and, when requested, one file per department named after the department.

## Script

Use `scripts/assign_dorms.py` as the starting point for real data runs. It accepts CSV inputs and emits CSV outputs:

```bash
python scripts/assign_dorms.py \
  --departments departments.csv \
  --rooms rooms.csv \
  --out-dir dorm_output
```

The script is a deterministic baseline allocator, not a full integer optimizer. If the user needs higher precision or many competing soft constraints, use it to normalize/validate inputs and then implement an OR-Tools or local-search optimization layer.

## Reporting Guidance

When generating Word reports, use the `documents` skill. Keep teacher-facing reports simple:
- one global summary document;
- one per-department document when requested;
- concrete room numbers, not ranges;
- mixed-room composition explicitly shown;
- unresolved constraints listed separately.

Do not assign individual students to beds unless the user explicitly provides a student roster and asks for bed-level output.
