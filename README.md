# WODIS - Workout Open Data Interchange Specification

> Your workout data should outlive your app and gym membership.

## Table of Contents

- [What is WODIS?](#what-is-wodis)
- [Quick Example](#quick-example)
- [The Data Hierarchy](#the-data-hierarchy)
- [Philosophy](#philosophy)
- [What You Record vs What You Learn](#what-you-record-vs-what-you-learn)
- [Conformance Levels](#conformance-levels)
- [Extensions (`_extra`)](#extensions-_extra)
- [For App Developers](#for-app-developers)
- [What Else Exists](#what-else-exists)
- [Contributing](#contributing)
- [License](#license)

---

## What is WODIS?

WODIS is a shared format for workout data so you can move your training history between apps without losing anything. Switch apps? Keep your logs.

It's also a push for training apps to stop treating your data as a retention strategy. When your logs are portable, apps earn you by being better, not by making it painful to leave.

WODIS is a JSON-based open specification. Ever exported a workout log and gotten a lossy CSV that flattened your supersets into meaningless rows? WODIS fixes that. It keeps your dropsets, supersets, per-rep data, and RPE intact. Not flattened. Not lossy.

It's a JSON file. Your data lives on your machine, not locked in someone's cloud. Open it in a text editor and read it. Analyze it with Python, Excel, whatever. Any tool that reads JSON reads WODIS.

Full field reference: [SPECIFICATION.md](SPECIFICATION.md) | Schema: [wodis.schema.json](wodis.schema.json)

## Quick Example

A minimal Level 1 file. One exercise, one set, only required fields:

```json
{
  "wodis_version": "1.0.0",
  "meta": {
    "source": "my-gym-app"
  },
  "session": {
    "started_at": "2026-02-26T07:30:00Z",
    "load_unit": "kg",
    "exercises": [
      {
        "display_name": "Bench Press",
        "started_at": "2026-02-26T07:32:00Z",
        "sets": [
          {
            "reps_completed": 8,
            "load": 80
          }
        ]
      }
    ]
  }
}
```

That's it. A complete, valid WODIS file.

## The Data Hierarchy

```
Metadata        spec version, source app, athlete
  └─ Session      one workout: start time, location, exercises
       └─ Exercise   a named movement with its sets
            └─ Set       a group of reps without meaningful rest
                 └─ Rep      the atom: one repetition with its own load and flags
```

- **Rep** - One repetition. Most apps don't need this level of detail, but when you do a dropset or get a spot on rep 9, this is where it lives. Each rep can track its own load, and whether it was assisted or partial.
- **Set** - A group of reps done without meaningful rest. If you rested, it's a new set. If you dropped the weight and kept going, same set.
- **Exercise** - A movement and its sets. "Bench Press: 3 sets." The timestamp on each exercise gives you the order you did them in.
- **Session** - One workout. When you started, when you finished, what you did.
- **Metadata** - The label on the file. Which app made it, which version of the spec, who the athlete is.

## Philosophy

> This section and below uses MUST, SHOULD, and MAY as defined in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119). Full normative spec: [SPECIFICATION.md](SPECIFICATION.md).

### Why JSON, not binary

A WODIS file MUST be something you can open in a text editor in 2040 and still understand. Binary formats like Garmin FIT require an SDK just to decode a set of bench press reps. If the SDK dies, your data becomes an opaque blob. JSON has no SDK. It has curly braces. Every language ships a parser, and gzip closes the size gap when it matters.

### Why the rep is the atom

Most apps treat the set as the smallest unit. WODIS goes one level deeper because sets can't faithfully represent what actually happens.

You bench 8 reps at 100 kg, drop to 80 kg for 4 more, and your spotter helps on the last rep. A set-atomic model forces you to split it into two fake "sets" (losing the no-rest fact) or merge it into one (losing the load change). With per-rep data, the truth is preserved:

```json
{
  "reps_completed": 12,
  "load": 100,
  "set_type": "dropset",
  "reps": [
    { "load": 100 },
    { "load": 100 },
    { "load": 100 },
    { "load": 100 },
    { "load": 100 },
    { "load": 100 },
    { "load": 100 },
    { "load": 100 },
    { "load": 80 },
    { "load": 80 },
    { "load": 80 },
    { "load": 80, "assisted": true }
  ]
}
```

The per-rep `reps[]` array is OPTIONAL. A simple app writes `reps_completed` and `load` at the set level and calls it a day. But the spec MUST support per-rep data for when someone needs it: a coach reviewing form breakdown, a researcher tracking velocity per rep.

### Why timestamps, not sequence numbers

If you store both a sequence number and a timestamp, you create two sources of truth for exercise order. Eventually they'll disagree. WODIS uses timestamps as the single source: sort by `started_at` to get exercise order. Timestamps carry more information than sequence numbers. From them you can derive order, rest periods, session duration, and time-of-day patterns. Store the richer data; derive the simpler view.

### Why `_extra`, not more fields

GPX has been the universal standard for GPS tracks for 20+ years. Its `<extensions>` tag let Garmin add heart rate and Strava add power data without changing the core spec. WODIS follows the same pattern. The core covers what every workout app needs: exercises, sets, reps, load, timestamps, RPE. Everything else (velocity, tempo, equipment config, recovery metrics) goes in `_extra`. The core stays simple enough to implement in a weekend.

### Why no exercise database

WODIS doesn't ship an exercise list. There's no canonical "Squat" vs "Back Squat" vs "Barbell Back Squat." Nobody agrees, and the best open database (wger) is copyleft, which would force licensing obligations onto every app.

WODIS standardizes workout *structure*, not exercise names. Apps bring their own lists. The spec provides `canonical_ids` hooks for cross-referencing when they need to.

### Philosophy summary

| Decision | Reasoning |
|---|---|
| JSON format | Human-readable in 2040, no SDK required, universal parser support |
| Rep as atom | Dropsets, assisted reps, and partial reps need per-rep granularity |
| Timestamps over sequence | Single source of truth, richer data, no contradiction risk |
| `_extra` over more fields | Core stays stable and simple. Apps extend at the edges |
| No exercise database | Licensing risk, naming disagreements, infinite taxonomy. Not our problem |

## What You Record vs What You Learn

WODIS draws a hard line between two things: what happened and what it means.

The file stores **ground truth** - things that disappear if you don't capture them in the moment. The app you use with WODIS data calculates **derived insights** from that ground truth.

**Ground truth (goes in the file):** timestamps, load, reps, RPE/RIR, superset relationships, rest periods, failure flags, assisted/partial rep flags.

**Derived insights (the app's job):** personal records, volume metrics, estimated 1RM, fatigue trends, progressive overload, muscle-group workload.

The file is the source of truth. The app is the analyst. You can always derive less, but you can't derive what was never recorded.

For a deeper look at common mistakes (inferring rest from timestamps, detecting supersets from timing, confusing velocity with RPE) and a worked example, see [Section 7 of the specification](SPECIFICATION.md#7-ground-truth-vs-derived-data).

## Conformance Levels

Not every app needs every field. WODIS defines three levels so you can pick the depth that fits.

### Level 1 - Minimal

The bare essentials. Enough to reconstruct what you did.

| Field | Location |
|---|---|
| `wodis_version` | root |
| `meta.source` | meta |
| `session.started_at` | session |
| `session.load_unit` | session |
| `exercise.display_name` | exercise |
| `exercise.started_at` | exercise |
| `set.reps_completed` | set |
| `set.load` | set |

A Level 1 file is what a simple logging app exports. Exercise name, when it happened, how many reps, how much weight. Valid and useful.

### Level 2 - Standard

What a serious training app SHOULD export. Adds everything needed to analyze training quality, not just volume.

All Level 1 fields, plus:

| Field | Location | Purpose |
|---|---|---|
| `set.rpe` | set | How hard the set felt |
| `set.rir` | set | Estimated reps in reserve |
| `set.set_type` | set | Working, warmup, dropset, failure, backoff, amrap |
| `set.rest_seconds_actual` | set | Actual rest taken before this set |
| `set.is_failure` | set | Whether the set reached muscular failure |
| `set.superset_id` | set | Groups sets into supersets |
| `set.superset_sequence` | set | Order within a superset |
| `exercise.muscle_groups` | exercise | Primary muscles targeted |
| `set.form_flags` | set | Form deviations observed |

### Level 3 - Rich

For research tools, velocity trackers, and advanced coaching platforms. Full per-rep atomic data plus app-specific extensions.

All Level 2 fields, plus:

| Field | Location | Purpose |
|---|---|---|
| `set.reps[]` | set | Per-rep atomic array with individual load, assisted, partial, completed flags |
| Any `_extra` data | any level | Velocity, tempo, equipment config, media, recovery metrics |

Level 3 makes full use of `_extra`. Per-rep velocity, eccentric tempo, cable height, bar type, video attachments.

### Round-trip rule

Regardless of your conformance level: if you import a file with fields you don't recognize, you MUST preserve them on export. A Level 1 app that reads a Level 3 file MUST NOT strip the Level 3 data. Don't drop someone else's data.

## Extensions (`_extra`)

Every object in WODIS (metadata, session, exercise, set, rep) has an `_extra` field for app-specific data that doesn't belong in the core schema.

### Three rules

1. **Preserve on round-trip.** If you import a file with `_extra` data you don't recognize, you MUST write it back out when exporting. Never drop someone else's data.
2. **Namespace by app.** Use `"_extra": { "myapp": { ... } }` to avoid collisions between different apps writing to the same `_extra` object.
3. **No validation.** The spec does not validate `_extra` contents. It's an open object. Validation is the responsibility of the app that wrote it.

### Example

Velocity tracking on a set:

```json
{
  "reps_completed": 5,
  "load": 120,
  "_extra": {
    "velocityapp": {
      "mean_concentric_velocity_ms": [0.75, 0.71, 0.65, 0.58, 0.50],
      "peak_velocity_ms": [1.02, 0.98, 0.91, 0.82, 0.71]
    }
  }
}
```

The same pattern works for tempo prescriptions, equipment configuration, recovery/readiness metrics, media attachments, or anything else your app tracks. Namespace it, and it rides along without touching the core schema.

## For App Developers

### Exporting to WODIS

```
function exportToWODIS(workout):
    file = {}
    file.wodis_version = "1.0.0"
    file.meta = { source: YOUR_APP_NAME }
    file.session = {
        started_at: workout.startTime,
        exercises: []
    }
    for each exercise in workout:
        entry = {
            display_name: exercise.name,
            started_at: exercise.startTime,
            sets: []
        }
        for each set in exercise:
            entry.sets.append({
                reps_completed: set.reps,
                load: set.weight
            })
        file.session.exercises.append(entry)
    return JSON.stringify(file)
```

### Importing from WODIS

```
function importFromWODIS(json):
    file = JSON.parse(json)
    for each exercise in file.session.exercises:
        for each set in exercise.sets:
            saveToDatabase(exercise.display_name, set)
    // IMPORTANT: preserve any _extra fields you don't recognize.
    // They belong to another app. Don't drop them on round-trip.
    saveRawJSON(file)
```

**If you don't recognize a field, keep it anyway.** `_extra` exists on every level (set, exercise, session, metadata, rep). Namespace your extensions (e.g., `"_extra": { "myapp": { ... } }`) and never delete someone else's.

## What Other Ideas Already Exist

- **[OpenWeight](https://openweight.dev)** - Closest prior art. Covers sets, RPE, supersets, tempo. Apache 2.0. WODIS adds per-rep atomicity and the record-vs-learn separation.
- **wger** - Open-source workout manager with a good data model, but it's an app API, not a portable interchange spec.
- **Garmin FIT** - Proprietary binary. Strong on cardio, limited for strength training.
- **GPX** - The inspiration. Simple, extensible, human-readable. The universal standard for GPS tracks.

## Contributing

Open a GitHub issue first to discuss the change. Once there's agreement, submit a pull request.

- If changing the schema: update the schema file, examples, and SPECIFICATION.md.
- If adding a new field: include a rationale for why it can't live in `_extra`.

Be respectful. Have fun.

### Versioning

WODIS follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **Patch** (1.0.x) - Typo fixes, clarifications. No schema changes.
- **Minor** (1.x.0) - New optional fields. Backward compatible.
- **Major** (x.0.0) - Breaking changes: removed fields, changed types, new required fields.

### Style

- JSON field names in `snake_case`
- Timestamps in ISO 8601
- Weight in kg or lbs (declared by `load_unit`)
- Durations in seconds

## License

[MIT](LICENSE)
