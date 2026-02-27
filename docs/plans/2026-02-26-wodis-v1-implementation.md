# WODIS v1.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship the first public version of the WODIS spec on GitHub — README, JSON Schema, example files, and core documentation.

**Architecture:** A pure documentation/specification repo. No application code. The JSON Schema is the machine-readable contract; the markdown docs are the human-readable guide. Example files prove the spec works against real workout data.

**Tech Stack:** JSON Schema (draft-07), Markdown, optional Python for schema validation testing

---

### Task 1: README.md — The Manifesto

**Files:**
- Create: `README.md`

**Step 1: Write the README**

The README is the front door. It must contain, in order:

1. **One-line pitch:** "Your workout data should outlive your gym membership."
2. **What is WODIS:** 2-3 sentences. JSON-based, strength training, data portability.
3. **Jobs it solves:** The 6 jobs from the design doc, written as user quotes.
4. **Philosophy:** The 3 principles (rep is the atom, record vs learn, use what you need).
5. **Quick example:** A minimal Level 1 JSON file (~15 lines) showing one exercise with one set.
6. **The 10-field core:** List of what's required vs optional.
7. **What You Record vs What You Learn:** Short summary with link to full doc.
8. **Conformance levels:** Level 1/2/3 one-liner each.
9. **For app developers:** 10-line pseudocode for exporting and importing.
10. **Prior art:** Brief acknowledgment of OpenWeight, wger, FIT.
11. **License:** MIT.

**Step 2: Commit**

```bash
git add README.md
git commit -m "Add README with spec overview, jobs, and quick example"
```

---

### Task 2: LICENSE

**Files:**
- Create: `LICENSE`

**Step 1: Write MIT license file**

Standard MIT license text with copyright holder name and year 2026.

**Step 2: Commit**

```bash
git add LICENSE
git commit -m "Add MIT license"
```

---

### Task 3: JSON Schema — The Contract

**Files:**
- Create: `wodis.schema.json`

**Step 1: Write the JSON Schema**

JSON Schema draft-07 implementing the full data hierarchy from the design doc:

- Top level: `wodis_version` (required), `meta` (required), `session` (required)
- `meta`: `source` (required), `entry_method`, `athlete`, `_extra`
- `session`: `started_at` (required), `ended_at`, `location`, `split_type`, `exercises[]` (required), `notes`, `_extra`
- `exercises[]`: `display_name` (required), `started_at` (required), `sets[]` (required), `canonical_ids`, `muscle_groups[]`, `variation`, `notes`, `_extra`
- `sets[]`: `reps_completed` (required), `load_kg` (required), `reps[]`, `set_type` (enum), `rpe`, `rir`, `rest_seconds_actual`, `is_failure`, `form_flags[]`, `superset_id`, `superset_sequence`, `transition_time_seconds`, `timestamp`, `notes`, `_extra`
- `reps[]`: `load_kg` (required), `assisted`, `partial`, `completed`
- `_extra` on every object: `type: object`, `additionalProperties: true`
- `additionalProperties: true` on all objects (forward compatibility)

Key validation rules:
- `set_type` enum: working, warmup, dropset, failure, backoff, amrap
- `rpe` minimum 1, maximum 10
- `rir` minimum 0, maximum 5
- `started_at` format: date-time
- `wodis_version` enum: ["1.0.0"]

**Step 2: Validate the schema is valid JSON Schema**

Run: `python -c "import json; json.load(open('wodis.schema.json'))"`
Expected: No error

**Step 3: Commit**

```bash
git add wodis.schema.json
git commit -m "Add WODIS v1.0.0 JSON Schema"
```

---

### Task 4: Minimal Example (Level 1)

**Files:**
- Create: `examples/minimal.json`

**Step 1: Write minimal example**

One exercise, one set, only required fields. Should be readable by a human in 5 seconds. Represents what a dead-simple logging app would export.

**Step 2: Validate against schema**

Run: `python -c "import json, jsonschema; schema = json.load(open('wodis.schema.json')); data = json.load(open('examples/minimal.json')); jsonschema.validate(data, schema); print('VALID')"`
Expected: VALID

If jsonschema is not installed: `pip install jsonschema` first.

**Step 3: Commit**

```bash
git add examples/minimal.json
git commit -m "Add minimal Level 1 example"
```

---

### Task 5: Standard Example (Level 2)

**Files:**
- Create: `examples/standard.json`

**Step 1: Write standard example**

A realistic push day with:
- 3-4 exercises
- Multiple sets per exercise with RPE
- A superset pair (e.g., bench + pull-ups with superset_id: "A")
- Different set types (warmup, working)
- Rest times
- Timestamps that show exercise order

**Step 2: Validate against schema**

Same validation command as Task 4.

**Step 3: Commit**

```bash
git add examples/standard.json
git commit -m "Add standard Level 2 example with supersets"
```

---

### Task 6: Advanced Example (Level 3)

**Files:**
- Create: `examples/advanced.json`

**Step 1: Write advanced example**

A session featuring:
- A dropset with per-rep atomic array (load changes mid-set, one rep is assisted, one is partial)
- Velocity data in `_extra`
- Equipment config in `_extra`
- Failure flags and form_flags
- Full metadata with entry_method and readiness context in `_extra`

**Step 2: Validate against schema**

Same validation command as Task 4.

**Step 3: Commit**

```bash
git add examples/advanced.json
git commit -m "Add advanced Level 3 example with per-rep data and dropsets"
```

---

### Task 7: Real-World Example From Actual Data

**Files:**
- Create: `examples/real-world/from-workout-log-app.json`

**Step 1: Convert one session from the user's actual SQLite data**

Take the 2026-02-26 push session (Bench, Shoulder Press, Skullcrushers, Side Laterals, Triceps Rope Pushdown) and convert it to WODIS format. This proves the spec works against real messy data.

Source: `Z:/Downloads/workoutlog.bak` SQLite database

**Step 2: Validate against schema**

Same validation command as Task 4.

**Step 3: Commit**

```bash
git add examples/real-world/from-workout-log-app.json
git commit -m "Add real-world example converted from actual workout data"
```

---

### Task 8: Philosophy Doc

**Files:**
- Create: `docs/philosophy.md`

**Step 1: Write philosophy doc**

Covers:
- Why JSON not binary (human-readable in 2040)
- Why the rep is the atom (dropset problem)
- Why timestamps not sequence numbers (derived vs recorded)
- Why _extra not more fields (GPX lesson)
- Why no exercise database (licensing, the "naming problem")
- Prior art acknowledgment (OpenWeight, wger, FIT, GPX)

**Step 2: Commit**

```bash
git add docs/philosophy.md
git commit -m "Add philosophy doc explaining design decisions"
```

---

### Task 9: What You Record vs What You Learn Doc

**Files:**
- Create: `docs/what-you-record.md`

**Step 1: Write the ground truth vs derived data guide**

This is the content we wrote during brainstorming:
- Table of "What You Record" fields and why each must be in the file
- Table of "What You Learn" metrics and how to calculate each from spec data
- The danger zone (common traps: calculating rest from timestamps, detecting supersets from short rest, calculating RPE from velocity)
- Concrete example: the freshness problem (lat pulldown after rows)
- Implementation checklist for exporters and importers

**Step 2: Commit**

```bash
git add docs/what-you-record.md
git commit -m "Add guide: What You Record vs What You Learn"
```

---

### Task 10: Extensions Doc

**Files:**
- Create: `docs/extensions.md`

**Step 1: Write extensions guide**

- The 3 rules (preserve on round-trip, namespace by app, no validation)
- Common extension patterns with JSON examples:
  - Per-rep velocity
  - Tempo notation
  - Equipment config
  - Media attachments
  - Recovery/readiness (Whoop, Oura)
  - Program context

**Step 2: Commit**

```bash
git add docs/extensions.md
git commit -m "Add extensions guide for _extra usage"
```

---

### Task 11: Conformance Levels Doc

**Files:**
- Create: `docs/conformance.md`

**Step 1: Write conformance doc**

- Level 1 (Minimal): Field list, who this is for, example
- Level 2 (Standard): Field list, who this is for, example
- Level 3 (Rich): Field list, who this is for, example
- How to claim conformance ("WODIS Level 2 Compatible")

**Step 2: Commit**

```bash
git add docs/conformance.md
git commit -m "Add conformance levels documentation"
```

---

### Task 12: CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

**Step 1: Write contribution guidelines**

- How to propose changes (GitHub issues first, then PRs)
- Schema change process (must update schema + examples + docs)
- Versioning policy (semver: breaking = major, new fields = minor, typos = patch)
- Style guide (JSON field names in snake_case, ISO 8601 dates, kg as default unit)

**Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "Add contribution guidelines"
```

---

### Task 13: CHANGELOG.md

**Files:**
- Create: `CHANGELOG.md`

**Step 1: Write initial changelog**

```markdown
# Changelog

## [1.0.0] - 2026-02-26

### Added
- Initial WODIS v1.0.0 specification
- JSON Schema (draft-07)
- Core documentation (philosophy, what-you-record, extensions, conformance)
- Example files (minimal, standard, advanced, real-world)
```

**Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "Add changelog for v1.0.0"
```

---

### Task 14: Schema Validation Test

**Files:**
- Create: `tests/validate_examples.py`

**Step 1: Write a validation script**

A simple Python script that loads the schema and validates every JSON file in `examples/` against it. Reports pass/fail per file.

**Step 2: Run it**

Run: `python tests/validate_examples.py`
Expected: All examples VALID

**Step 3: Commit**

```bash
git add tests/validate_examples.py
git commit -m "Add schema validation test for all examples"
```

---

### Task 15: Final Review and Tag

**Step 1: Verify repo structure matches design doc**

Run: `find . -type f | grep -v .git | sort`
Confirm all planned files exist.

**Step 2: Read through README one more time**

Spot-check: Does the quick example validate against the schema? Do all internal links work?

**Step 3: Tag v1.0.0**

```bash
git tag -a v1.0.0 -m "WODIS v1.0.0 - Initial release"
```
