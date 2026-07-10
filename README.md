# Dorm Assignment Skill

Codex skill for department-level dormitory assignment.

## What It Does

This skill helps generate dorm allocation plans from department headcounts and room inventory data. It supports:

- separate male/female allocation models;
- fixed 6-person room capacity;
- department-level reports instead of bed-level assignments;
- small-department clustering;
- middle-floor and sunny-room preferences;
- remainder stitching within the same building;
- opposite-door room preference;
- validation outputs for assigned headcounts.

## Install

Copy the `dorm-assignment` directory into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R dorm-assignment ~/.codex/skills/
```

Restart Codex or open a new session so the skill can be discovered.

## Required Inputs

Department CSV:

```csv
department,gender,count
计算机学院,男,310
计算机学院,女,176
```

Room CSV:

```csv
gender,building,block,building_id,floor,room,capacity,opposite_room_id
女,林曦楼,A,林曦楼A栋,3,301,6,林曦楼A栋-3-302
女,林曦楼,A,林曦楼A栋,3,302,6,林曦楼A栋-3-301
男,暖煦楼,,暖煦楼,4,401,6,暖煦楼-4-402
```

## Baseline Script

```bash
python dorm-assignment/scripts/assign_dorms.py \
  --departments departments.csv \
  --rooms rooms.csv \
  --out-dir dorm_output
```

Outputs:

- `assignments.csv`
- `mixed_rooms.csv`
- `validation.csv`

The script is a deterministic baseline allocator. For complex production allocation with many competing soft constraints, use it as the input normalizer and validation base, then add an optimizer layer.
