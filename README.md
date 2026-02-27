# WODIS - Workout Open Data Interchange Specification

> Your workout data should outlive your gym membership.

This document uses the keywords MUST, SHOULD, and MAY as defined in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119). For the full normative specification, see [SPECIFICATION.md](SPECIFICATION.md).

## Table of Contents

- [What is WODIS?](#what-is-wodis)
- [Jobs It Solves](#jobs-it-solves)
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

WODIS is a JSON-based open specification for storing and exchanging strength training data between apps. A common format so your workout history isn't trapped in one app forever.

Ever exported a workout log and gotten a lossy CSV that flattened your supersets into meaningless rows? WODIS fixes that.

Formal field reference: [SPECIFICATION.md](SPECIFICATION.md). Schema: [wodis.schema.json](wodis.schema.json).

## Jobs It Solves

| What you say | What WODIS does |
|---|---|
| "I want to switch apps without starting from scratch" | Move your workout history between apps with zero data loss |
| "I want my data on my machine, not locked in someone's cloud" | Own your training data in a plain JSON file you control |
| "I want to know why today felt harder than last week" | Timestamps, RPE, exercise order, and rest times are all in the file |
| "I want to use Python/Excel/whatever on my own data" | It's JSON. Any tool can read it |
| "My dropsets and supersets should look like dropsets and supersets, not flattened rows" | The structure stays intact |
| "I just want a schema to start from" | Validate against the schema and ship |

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
    "exercises": [
      {
        "display_name": "Bench Press",
        "started_at": "2026-02-26T07:32:00Z",
        "sets": [
          {
            "reps_completed": 8,
            "load_kg": 80
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

- **Rep** - The smallest unit. Each rep can have its own `load_kg`, `assisted`, and `partial` flags. Most apps won't need per-rep detail, but when you do a dropset or get a spot on rep 9, this is where it lives.
- **Set** - Reps done without meaningful rest. If you rested, it's a new set. If you dropped the weight and kept going, same set. Carries load, reps, RPE, set type, and optional per-rep breakdown.
- **Exercise** - A named movement with a timestamp and an array of sets. `started_at` lets apps derive exercise order without a fragile sequence number.
- **Session** - The workout. Start time, optional end time, location, and exercises.
- **Metadata** - The envelope. Schema version, which app created the file, optional athlete identifier.

## Philosophy

### Why JSON, not binary

A WODIS file MUST be something you can open in a text editor in 2040 and still understand. Binary formats like Garmin FIT require an SDK just to decode a set of bench press reps. If the SDK dies, your data becomes an opaque blob. JSON has no SDK. It has curly braces. Every language ships a parser, and gzip closes the size gap when it matters.

### Why the rep is the atom

Most apps treat the set as the smallest unit. WODIS goes one level deeper because sets can't faithfully represent what actually happens.

You bench 8 reps at 100 kg, drop to 80 kg for 4 more, and your spotter helps on the last rep. A set-atomic model forces you to split it into two fake "sets" (losing the no-rest fact) or merge it into one (losing the load change). With per-rep data, the truth is preserved:

```json
{
  "reps_completed": 12,
  "load_kg": 100,
  "set_type": "dropset",
  "reps": [
    { "load_kg": 100 },
    { "load_kg": 100 },
    { "load_kg": 100 },
    { "load_kg": 100 },
    { "load_kg": 100 },
    { "load_kg": 100 },
    { "load_kg": 100 },
    { "load_kg": 100 },
    { "load_kg": 80 },
    { "load_kg": 80 },
    { "load_kg": 80 },
    { "load_kg": 80, "assisted": true }
  ]
}
```

The per-rep `reps[]` array is OPTIONAL. A simple app writes `reps_completed` and `load_kg` at the set level and calls it a day. But the spec MUST support per-rep data for when someone needs it: a coach reviewing form breakdown, a researcher tracking velocity per rep.

### Why timestamps, not sequence numbers

If you store both a sequence number and a timestamp, you create two sources of truth for exercise order. Eventually they'll disagree. WODIS uses timestamps as the single source: sort by `started_at` to get exercise order. Timestamps carry more information than sequence numbers. From them you can derive order, rest periods, session duration, and time-of-day patterns. Store the richer data; derive the simpler view.

### Why `_extra`, not more fields

GPX has been the universal standard for GPS tracks for 20+ years. Its `<extensions>` tag let Garmin add heart rate and Strava add power data without changing the core spec. WODIS follows the same pattern. The core covers what every workout app needs: exercises, sets, reps, load, timestamps, RPE. Everything else (velocity, tempo, equipment config, recovery metrics) goes in `_extra`. The core stays simple enough to implement in a weekend.

### Why no exercise database

No canonical list of exercise names is baked into the spec. The most comprehensive open exercise database (wger's) is CC BY-SA. Bundling it would force copyleft obligations onto every app using WODIS. Beyond licensing, there's no consensus on naming ("Squat" vs "Back Squat" vs "Barbell Back Squat") and infinite variation disputes (is close-grip bench a separate exercise or a variation?). WODIS standardizes workout *structure*, not exercise semantics. Apps bring their own exercise lists. The spec provides `canonical_ids` hooks for cross-referencing.

### Philosophy summary

| Decision | Reasoning |
|---|---|
| JSON format | Human-readable in 2040, no SDK required, universal parser support |
| Rep as atom | Dropsets, assisted reps, and partial reps need per-rep granularity |
| Timestamps over sequence | Single source of truth, richer data, no contradiction risk |
| `_extra` over more fields | Core stays stable and simple. Apps extend at the edges |
| No exercise database | Licensing risk, naming disagreements, infinite taxonomy. Not our problem |

## What You Record vs What You Learn

The file stores **ground truth**: things that disappear if you don't capture them in the moment. The app calculates **derived insights** from that ground truth. These two categories MUST NOT be confused.

### Ground truth (goes in the file)

- Timestamps (when each exercise and set happened)
- Load (how much weight, per set or per rep)
- Reps completed
- RPE / RIR (how hard it felt, recorded at the moment of effort)
- Superset relationships (which exercises were paired)
- Rest periods (actual measured time, not planned)
- Failure and form observations
- Assisted / partial rep flags

### Derived insights (the app's job)

- Personal records (1RM, volume PRs)
- Volume metrics (tonnage, sets per muscle group)
- Estimated 1RM (Epley, Brzycki)
- Fatigue and freshness context
- Progressive overload trends
- Muscle-group workload distribution

The file is the source of truth. The app is the analyst.

### The Danger Zone

Three common traps where apps try to derive ground truth instead of recording it:

**1. Calculating rest from timestamps loses intent.**
Timestamps at 10:30:00 and 10:32:30 give you "150 seconds rest." But was that intentional rest, or 90 seconds of chatting? The rest the lifter chose to take is ground truth. Record it in `rest_seconds_actual`. Timestamp math is a backup, not a replacement.

**2. Detecting supersets from short rest is unreliable.**
15 seconds between a bench set and a row set looks like a superset. But maybe the lifter just moves fast between straight sets. Superset relationships are intentional structure. Record them with `superset_id` and `superset_sequence`. Don't infer intent from timing.

**3. Calculating RPE from velocity misses subjective experience.**
Velocity-based training can estimate effort from bar speed, but RPE is how hard the set *felt*. A lifter who slept 4 hours will rate RPE 8 on a set that would be a 6 on a good day, same velocity. Velocity is data (put it in `_extra`). RPE is perception (put it in `rpe`). They complement each other. One doesn't replace the other.

### Example: why did your lat pulldown drop off?

You log a pull day. Lat pulldown performance dropped: fewer reps, higher RPE, earlier failure than last week. Why? Here's what the file captured:

```json
{
  "wodis_version": "1.0.0",
  "meta": { "source": "pullday-tracker" },
  "session": {
    "started_at": "2026-02-26T07:00:00Z",
    "exercises": [
      {
        "display_name": "Barbell Row",
        "started_at": "2026-02-26T07:02:00Z",
        "muscle_groups": ["lats", "rhomboids", "biceps"],
        "sets": [
          { "reps_completed": 10, "load_kg": 80, "rpe": 7 },
          { "reps_completed": 10, "load_kg": 80, "rpe": 8 },
          { "reps_completed": 8, "load_kg": 80, "rpe": 9 }
        ]
      },
      {
        "display_name": "Chin-Up",
        "started_at": "2026-02-26T07:18:00Z",
        "muscle_groups": ["lats", "biceps"],
        "sets": [
          { "reps_completed": 8, "load_kg": 0, "rpe": 8 },
          { "reps_completed": 7, "load_kg": 0, "rpe": 9 },
          { "reps_completed": 5, "load_kg": 0, "rpe": 10, "is_failure": true }
        ]
      },
      {
        "display_name": "Lat Pulldown",
        "started_at": "2026-02-26T07:35:00Z",
        "muscle_groups": ["lats", "biceps"],
        "sets": [
          { "reps_completed": 8, "load_kg": 60, "rpe": 8 },
          { "reps_completed": 6, "load_kg": 60, "rpe": 9 },
          { "reps_completed": 5, "load_kg": 60, "rpe": 10, "is_failure": true }
        ]
      }
    ]
  }
}
```

The file doesn't say *why*. But it gives the app everything it needs to figure it out:

- **Three exercises sharing "lats"** - rows, chin-ups, and pulldowns all hit the same muscle.
- **Escalating RPE** - started at RPE 7 on rows, hit RPE 10 failure on chin-ups, already at RPE 8 on the *first* set of pulldowns.
- **Pre-fatigue** - by the time pulldowns started, the lats had done 6 hard sets across two exercises.

The app can show: "Your lats had 6 sets of work before pulldowns. Last week you did pulldowns second, not third." That's a derived insight. The file stored the facts: timestamps, exercise order, muscle groups, RPE per set.

If the file had only stored "lat pulldown: 3 sets" without timestamps, order, or muscle groups, the app could never reconstruct this. You can always derive less, but you can't derive what was never recorded.

## Conformance Levels

Not every app needs every field. WODIS defines three levels so you can pick the depth that fits.

### Level 1 - Minimal

The bare essentials. Enough to reconstruct what you did.

| Field | Location |
|---|---|
| `wodis_version` | root |
| `meta.source` | meta |
| `session.started_at` | session |
| `exercise.display_name` | exercise |
| `exercise.started_at` | exercise |
| `set.reps_completed` | set |
| `set.load_kg` | set |

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

### Common patterns

**Velocity data** (per-rep, in `_extra` on the set or rep):

```json
{
  "reps_completed": 5,
  "load_kg": 120,
  "_extra": {
    "velocityapp": {
      "mean_concentric_velocity_ms": [0.75, 0.71, 0.65, 0.58, 0.50],
      "peak_velocity_ms": [1.02, 0.98, 0.91, 0.82, 0.71]
    }
  }
}
```

**Tempo prescription** (on the set):

```json
{
  "reps_completed": 8,
  "load_kg": 60,
  "_extra": {
    "tempoapp": {
      "tempo": "3-1-2-0",
      "tempo_parts": {
        "eccentric_seconds": 3,
        "pause_bottom_seconds": 1,
        "concentric_seconds": 2,
        "pause_top_seconds": 0
      }
    }
  }
}
```

**Equipment configuration** (on the exercise):

```json
{
  "display_name": "Cable Fly",
  "started_at": "2026-02-26T08:00:00Z",
  "_extra": {
    "cableapp": {
      "machine": "functional_trainer",
      "pulley_height": "high",
      "handle_type": "D-handle",
      "cable_position": "both"
    }
  }
}
```

**Recovery and readiness** (on the session):

```json
{
  "started_at": "2026-02-26T07:00:00Z",
  "_extra": {
    "recoveryapp": {
      "hrv_rmssd_ms": 62,
      "sleep_hours": 7.5,
      "readiness_score": 78,
      "soreness_rating": 3
    }
  }
}
```

**Media attachments** (on the set):

```json
{
  "reps_completed": 3,
  "load_kg": 140,
  "_extra": {
    "formcheck": {
      "video_url": "https://example.com/clips/deadlift-pr.mp4",
      "thumbnail_url": "https://example.com/clips/deadlift-pr-thumb.jpg",
      "recorded_at": "2026-02-26T08:15:00Z"
    }
  }
}
```

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
                load_kg: set.weight
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

## What Else Exists

- **[OpenWeight](https://openweight.dev)** - Closest prior art. Covers sets, RPE, supersets, tempo. Apache 2.0. WODIS adds per-rep atomicity and the record-vs-learn separation.
- **wger** - Open-source workout manager with a good data model, but it's an app API, not a portable interchange spec.
- **Garmin FIT** - Proprietary binary. Strong on cardio, limited for strength training.
- **GPX** - The inspiration. Simple, extensible, human-readable. The universal standard for GPS tracks.

## Contributing

Open a GitHub issue first to discuss the change. Once there's agreement, submit a pull request.

- If changing the schema: update the schema file, examples, and SPECIFICATION.md.
- If adding a new field: include a rationale for why it can't live in `_extra`.

### Versioning

WODIS follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **Patch** (1.0.x) - Typo fixes, clarifications. No schema changes.
- **Minor** (1.x.0) - New optional fields. Backward compatible.
- **Major** (x.0.0) - Breaking changes: removed fields, changed types, new required fields.

### Style

- JSON field names in `snake_case`
- Timestamps in ISO 8601
- Weight in kilograms
- Durations in seconds

Be respectful. Have fun. And focus on helping better solve the user jobs that this product seeks to address.

## License

[MIT](LICENSE)
