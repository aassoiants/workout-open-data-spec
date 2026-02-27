# WODIS — Workout Open Data Interchange Specification

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
- [Prior Art](#prior-art)
- [License](#license)

---

## What is WODIS?

WODIS is a JSON-based open specification for storing and exchanging strength training data between apps. Think of it as the GPX of strength training: a common format so your workout history isn't trapped in one app forever. If you've ever exported a workout log and gotten a lossy CSV that flattened your supersets into meaningless rows, WODIS is the fix.

For the formal field-by-field reference, see [SPECIFICATION.md](SPECIFICATION.md). Validate your files against [wodis.schema.json](wodis.schema.json).

## Jobs It Solves

| What you say | What WODIS does |
|---|---|
| "I want to switch apps without starting from scratch" | Move your workout history between apps with zero data loss |
| "I want my data on my machine, not locked in someone's cloud" | Own your training data in a plain JSON file you control |
| "I want to know why today felt harder than last week" | Understand your performance in context — timestamps, RPE, exercise order, and rest times are all in the file |
| "I want to use Python/Excel/whatever on my own data" | Analyze your training your way — it's JSON, so any tool can read it |
| "My dropsets and supersets should look like dropsets and supersets, not flattened rows" | Keep a faithful record of what you actually did, with the structure intact |
| "I just want a schema to start from" | Build fitness tools without reinventing the wheel — validate against the schema and ship |

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
Metadata          — The envelope: spec version, source app, athlete
  └─ Session      — One workout: start time, location, exercises
       └─ Exercise   — A named movement: "Bench Press", with its sets
            └─ Set       — A group of reps without meaningful rest
                 └─ Rep      — The atom: one repetition with its own load and flags
```

- **Rep** — The smallest unit. Each rep can have its own `load_kg`, `assisted`, and `partial` flags. Most apps won't need per-rep detail, but when you do a dropset or get a spot on rep 9, this is where it lives.
- **Set** — A collection of reps done without meaningful rest. If you rested, it's a new set. If you dropped the weight and kept going, it's the same set. Carries load, reps completed, RPE, set type, and optional per-rep breakdown.
- **Exercise** — A named movement with a timestamp and an array of sets. The `started_at` field lets apps derive exercise order without a fragile sequence number.
- **Session** — The workout itself. Start time, optional end time, location, and the array of exercises you did.
- **Metadata** — The envelope around everything. Schema version, which app created the file, and an optional athlete identifier.

## Philosophy

### Why JSON, not binary

A WODIS file MUST be something you can open in a text editor in 2040 and still understand. Binary formats like Garmin FIT require an SDK just to decode a set of bench press reps — if the SDK dies, your data becomes an opaque blob. JSON has no SDK. It has curly braces. Every language ships a parser, and gzip closes the size gap when it matters.

### Why the rep is the atom

Most apps treat the set as the smallest unit. WODIS goes one level deeper because sets can't faithfully represent what actually happens. Consider: you bench 8 reps at 100 kg, drop to 80 kg for 4 more, and your spotter helps on the last rep. A set-atomic model forces you to split it into two fake "sets" (losing the fact there was no rest) or merge it into one (losing the load change). With rep-level atomicity, the truth is preserved:

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

The per-rep `reps[]` array is OPTIONAL. A simple app writes `reps_completed` and `load_kg` at the set level and calls it a day. But the spec MUST support per-rep data because when someone needs it — a coach reviewing form breakdown, a researcher tracking velocity per rep — the model is already there.

### Why timestamps, not sequence numbers

If you store both a sequence number and a timestamp, you create two sources of truth for exercise order. Eventually they will disagree. WODIS uses timestamps as the single source of truth: sort by `started_at` to get exercise order. A timestamp also carries more information than a sequence number — from it you can derive order, rest periods, session duration, and time-of-day patterns. Store the richer data; derive the simpler view.

### Why `_extra`, not more fields

GPX has stayed the universal standard for GPS tracks for 20+ years because its `<extensions>` tag let Garmin add heart rate and Strava add power data without changing the core spec. WODIS follows the same pattern. The core schema covers what every workout app needs: exercises, sets, reps, load, timestamps, RPE. Everything else — velocity, tempo, equipment config, recovery metrics — goes in `_extra`. The core stays simple enough to implement in a weekend. Innovation happens at the edges.

### Why no exercise database

There is no canonical list of exercise names baked into the spec. The most comprehensive open exercise database (wger's) is CC BY-SA — bundling it would force copyleft obligations onto every app using WODIS. Beyond licensing, there is no consensus on naming ("Squat" vs "Back Squat" vs "Barbell Back Squat") and infinite variation disputes (is close-grip bench a separate exercise or a variation?). WODIS standardizes workout *structure*, not exercise semantics. Apps bring their own exercise lists; the spec provides `canonical_ids` hooks for cross-referencing.

### Philosophy summary

| Decision | Reasoning |
|---|---|
| JSON format | Human-readable in 2040, no SDK required, universal parser support |
| Rep as atom | Dropsets, assisted reps, and partial reps need per-rep granularity |
| Timestamps over sequence | Single source of truth, richer data, no contradiction risk |
| `_extra` over more fields | Core stays stable and simple; innovation happens at the edges |
| No exercise database | Licensing risk, naming disagreements, infinite taxonomy — not our problem |

## What You Record vs What You Learn

This is the core principle of WODIS. The file stores **ground truth** — things that disappear if you don't capture them in the moment. The app calculates **derived insights** from that ground truth. These two categories MUST NOT be confused.

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
If you record set timestamps at 10:30:00 and 10:32:30, an app can calculate "150 seconds rest." But was that 150 seconds of intentional rest, or did you spend 90 seconds chatting and only intended 60 seconds? The *actual* rest the lifter chose to take is ground truth. Record it in `rest_seconds_actual`. Timestamp math is a backup, not a replacement.

**2. Detecting supersets from short rest is unreliable.**
An app that sees 15 seconds between a bench press set and a barbell row set might guess "superset." But maybe the lifter just moves fast between straight sets. Maybe they were resting 2 minutes and got interrupted. Superset relationships are intentional structure — record them with `superset_id` and `superset_sequence`. Don't infer intent from timing coincidence.

**3. Calculating RPE from velocity misses subjective experience.**
Velocity-based training can estimate effort from bar speed, but RPE is a subjective measure of how hard the set *felt*. A lifter who slept 4 hours will rate an 8 RPE on a set that would be a 6 on a good day, even at the same velocity. Velocity is data (put it in `_extra`). RPE is perception (put it in `rpe`). They complement each other; one does not replace the other.

### Concrete example: "Your lat pulldown sucked today — why?"

You log a pull day. Your lat pulldown performance dropped — fewer reps, higher RPE, earlier failure than last week. Why? Here's what the WODIS file captured:

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

The file doesn't tell you *why* the lat pulldown dropped off. But it gives the app everything it needs to figure it out. The app can see:

- **Three exercises sharing "lats"** — barbell rows, chin-ups, and lat pulldowns all hit the same primary mover.
- **Escalating RPE curve** — the lifter started at RPE 7 on rows, hit RPE 10 failure on chin-ups, and was already at RPE 8 on the *first* set of pulldowns.
- **Pre-fatigue is the obvious explanation** — by the time lat pulldowns started, the lats had already done 6 hard sets across two exercises.

The app can calculate "cumulative lat volume before this exercise" and show a freshness estimate: "Your lats had already taken 6 sets of work before pulldowns. Last week you did pulldowns second, not third." That insight is derived. The file stored the facts — timestamps, exercise order, muscle groups, RPE per set. The separation works.

If the file had only stored "lat pulldown: 3 sets" without timestamps, exercise order, or muscle groups, the app could never reconstruct the pre-fatigue story. Ground truth enables insight. You can always derive less, but you can't derive what was never recorded.

## Conformance Levels

Not every app needs every field. WODIS defines three levels so you can pick the depth that fits.

### Level 1 — Minimal

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

### Level 2 — Standard

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

### Level 3 — Rich

For research tools, velocity trackers, and advanced coaching platforms. Full per-rep atomic data plus app-specific extensions.

All Level 2 fields, plus:

| Field | Location | Purpose |
|---|---|---|
| `set.reps[]` | set | Per-rep atomic array with individual load, assisted, partial, completed flags |
| Any `_extra` data | any level | Velocity, tempo, equipment config, media, recovery metrics |

Level 3 is where `_extra` earns its keep. Per-rep velocity, eccentric tempo, cable height, bar type — all of it lives here.

### Round-trip rule

Regardless of your conformance level: if you import a file with fields you don't recognize, you MUST preserve them on export. A Level 1 app that reads a Level 3 file MUST NOT strip the Level 3 data. Don't drop someone else's data.

## Extensions (`_extra`)

Every object in WODIS — metadata, session, exercise, set, rep — has an `_extra` field. This is the escape hatch for app-specific data that doesn't belong in the core schema.

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

The golden rule of import: **if you don't recognize a field, keep it anyway.** The `_extra` object on every level (set, exercise, session, metadata) is the escape hatch for app-specific data. Namespace your extensions (e.g., `"_extra": { "myapp": { ... } }`) and never delete someone else's.

## Prior Art

WODIS didn't emerge in a vacuum. We looked at what exists:

- **[OpenWeight](https://openweight.dev)** — The closest prior art. Covers sets, RPE, supersets, and tempo. Apache 2.0 licensed. WODIS adds per-rep atomicity and the "What You Record vs What You Learn" separation.
- **wger** — A rich open-source workout manager with a good data model, but it's an application API, not a portable interchange spec.
- **Garmin FIT** — Proprietary binary format. Strong on cardio, limited and poorly documented for strength training.
- **GPX** — The inspiration for WODIS's approach: a simple, extensible, human-readable format that became the universal standard for GPS tracks. We want to do the same for the barbell.

## License

[MIT](LICENSE)
