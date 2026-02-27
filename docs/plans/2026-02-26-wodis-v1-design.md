# WODIS v1.0 Design Document

## Workout Open Data Interchange Specification

**Date:** 2026-02-26
**Status:** Approved for first pass implementation

---

## What Is WODIS?

A JSON-based open specification that defines how strength training data is structured, stored, and exchanged between apps. The GPX of lifting.

## Philosophy

1. **The rep is the atom.** Every structure (set, exercise, session) is a container of reps. A rep carries its own load, assisted flag, and partial flag — because a dropset rep at 60lbs is not the same as a working rep at 100lbs.
2. **Record what happened, not what it means.** The spec stores ground truth ("What You Record"). Derived insights like PRs and volume trends ("What You Learn") are the app's job.
3. **Use what you need, ignore what you don't.** Conformance levels let a simple logger write 3 fields while a velocity lab writes 20. Unknown fields are preserved on round-trip.

## Jobs This Solves

1. **Move my workout history between apps** — "I want to switch apps without starting from scratch"
2. **Own my training data** — "I want my data on my machine, not locked in someone's cloud"
3. **Understand my performance in context** — "I want to know why today felt harder than last week"
4. **Analyze my training my way** — "I want to use Python/Excel/whatever on my own data"
5. **Keep a faithful record of what I actually did** — "My dropsets and supersets should look like dropsets and supersets, not flattened rows"
6. **Build fitness tools without reinventing the wheel** — "I just want a schema to start from"

## Prior Art

No open strength training data interchange spec exists:
- **Garmin FIT**: Proprietary binary, poorly documented for strength
- **wger API**: Rich data model but it's an app API, not a portable spec
- **Hevy/Strong CSV**: Proprietary, lossy (flattens supersets, drops RPE)
- **HL7 FHIR**: Explicitly punted on strength training granularity
- **OpenWeight (openweight.dev)**: Closest prior art. Covers sets/RPE/supersets/tempo. But no per-rep atomicity, no assisted/partial reps, no exercise sequencing for freshness context. Apache 2.0.

WODIS is differentiated by per-rep granularity and the "What You Record vs What You Learn" philosophy.

## License

MIT. Can upgrade to Apache 2.0 later if corporate contributors emerge.

## Data Hierarchy

### Rep (the atom)

The smallest indivisible unit. Each rep can differ from its neighbors (load, assistance, range of motion).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `load_kg` | number | yes | Weight moved. Can change mid-set (dropsets) |
| `assisted` | boolean | no | Spotter or machine assisted |
| `partial` | boolean | no | Incomplete range of motion |
| `completed` | boolean | no | Did the rep finish |

### Set (collection of reps without meaningful rest)

If you rested, it's a new set. If you dropped the pin and kept going, it's the same set.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reps_completed` | integer | yes | Total count (always present) |
| `load_kg` | number | yes | Weight for the set (when all reps share same load) |
| `reps[]` | array | no | Optional per-rep atomic array (for apps that track granularly) |
| `set_type` | string | no | working, warmup, dropset, failure, backoff, AMRAP |
| `rpe` | number | no | Rate of perceived exertion (1-10) |
| `rir` | number | no | Reps in reserve (0-5) |
| `rest_seconds_actual` | number | no | Time rested before this set |
| `is_failure` | boolean | no | Hit failure? |
| `form_flags[]` | array | no | Technique observations |
| `superset_id` | string | no | Links alternating exercises ("A", "B") |
| `superset_sequence` | integer | no | Order within superset group |
| `transition_time_seconds` | number | no | Time to switch exercises in superset |
| `timestamp` | string | no | ISO 8601 per-set timestamp (recommended) |
| `notes` | string | no | Free text |
| `_extra` | object | no | App-specific data (must be preserved on round-trip) |

### Exercise (named movement with sets)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | yes | User-facing label |
| `canonical_ids` | object | no | Reference IDs (wger, exercisedb, app-specific) |
| `muscle_groups[]` | array | no | Primary muscles targeted (enables freshness calculation) |
| `variation` | string | no | Descriptive tags (high_bar, close_grip, deficit) |
| `started_at` | string | yes | ISO 8601 timestamp (exercise sequence derived from this) |
| `sets[]` | array | yes | Array of sets |
| `notes` | string | no | Free text |
| `_extra` | object | no | App-specific data |

### Session (the workout)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `started_at` | string | yes | ISO 8601 timestamp |
| `ended_at` | string | no | ISO 8601 timestamp |
| `location` | string | no | Gym name or free text |
| `split_type` | string | no | upper/lower, PPL, full body |
| `exercises[]` | array | yes | Array of exercises |
| `notes` | string | no | Free text |
| `_extra` | object | no | App-specific data |

### Metadata (the envelope)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `wodis_version` | string | yes | Schema version ("1.0.0") |
| `source` | string | yes | App or method that recorded this |
| `entry_method` | string | no | manual, device_sync, imported_csv |
| `athlete` | string | no | Identifier |
| `_extra` | object | no | App-specific data (readiness, sleep, recovery scores) |

## What You Record vs What You Learn

### What You Record (must be in the file)

Ground truth that disappears if not captured in the moment:
- Timestamps (per-exercise minimum, per-set recommended)
- Load per set (or per rep for dropsets)
- Reps completed
- RPE/RIR (subjective, recorded at moment of effort)
- Superset relationships (structural intent, not derivable)
- Rest periods (actual measured, not planned)
- Failure/form observations
- Assistance/partial flags
- Muscle groups (needed for freshness calculation)
- Data provenance (source app, entry method)

### What You Learn (apps calculate this)

Derivable from workout files + historical files:
- Personal records (1RM, 5RM, volume, daily tonnage)
- Exercise sequence (derived from timestamps)
- Volume metrics (tonnage, volume per muscle group)
- Fatigue/freshness context (sequence + muscle groups + preceding work)
- Estimated 1RM (Epley/Brzycki formula)
- Progressive overload trends
- Deload detection
- Training density

## Extensions (_extra)

The GPX-style escape hatch. Present on every object (set, exercise, session, metadata).

Rules:
1. Always preserve on round-trip (never drop unknown fields)
2. Namespace by app name to avoid collisions
3. No validation by the spec

Common patterns:
- Per-rep velocity data
- Tempo notation
- Equipment config (cable height, bar type, bench angle)
- Media attachments (video URIs)
- Recovery/readiness scores (Whoop, Oura)
- Program context (mesocycle week, training block)

## Conformance Levels

- **Level 1 (Minimal):** wodis_version, meta.source, meta.when, exercise.display_name, exercise.started_at, set.reps_completed, set.load_kg
- **Level 2 (Standard):** + RPE/RIR, superset_id, rest_seconds, set_type, muscle_groups, failure flags
- **Level 3 (Rich):** + Per-rep atomic array, equipment config in _extra, velocity data, media attachments

## Repository Structure

```
wodis-spec/
  README.md              — The manifesto + jobs + quick example
  LICENSE                — MIT
  CONTRIBUTING.md        — How to propose changes
  CHANGELOG.md           — Version history
  wodis.schema.json      — JSON Schema (the contract)
  docs/
    philosophy.md        — Why we made the choices we made
    what-you-record.md   — Ground truth vs derived data guide
    extensions.md        — How to use _extra properly
    conformance.md       — Level 1 vs 2 vs 3
  examples/
    minimal.json         — Level 1 example
    standard.json        — Level 2 with supersets
    advanced.json        — Level 3 with per-rep data
    real-world/
      from-strong-csv.json
      from-hevy-csv.json
```

## What's NOT in V1

- Exercise database/taxonomy (apps bring their own)
- Converter tools (separate repos, future work)
- SDKs (future work)
- Cardio/endurance data (strength-first, expand later)
- Formal RFC governance (solo maintainer for now, semver versioning)
