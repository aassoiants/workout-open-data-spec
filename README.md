# WODIS — Workout Open Data Interchange Specification

> Your workout data should outlive your gym membership.

## What is WODIS?

WODIS is a JSON-based open specification for storing and exchanging strength training data between apps. Think of it as the GPX of strength training: a common format so your workout history isn't trapped in one app forever. If you've ever exported a workout log and gotten a lossy CSV that flattened your supersets into meaningless rows, WODIS is the fix.

## Jobs It Solves

| What you say | What WODIS does |
|---|---|
| "I want to switch apps without starting from scratch" | Move your workout history between apps with zero data loss |
| "I want my data on my machine, not locked in someone's cloud" | Own your training data in a plain JSON file you control |
| "I want to know why today felt harder than last week" | Understand your performance in context — timestamps, RPE, exercise order, and rest times are all in the file |
| "I want to use Python/Excel/whatever on my own data" | Analyze your training your way — it's JSON, so any tool can read it |
| "My dropsets and supersets should look like dropsets and supersets, not flattened rows" | Keep a faithful record of what you actually did, with the structure intact |
| "I just want a schema to start from" | Build fitness tools without reinventing the wheel — validate against the schema and ship |

## Philosophy

**1. The rep is the atom.**
The rep is the smallest indivisible unit in WODIS. Every rep can carry its own load, its own assisted flag, its own partial flag. A dropset rep at 60 lbs is not the same as a working rep at 100 lbs, and the spec doesn't pretend they are. Sets are containers of reps. Exercises are containers of sets. Sessions are containers of exercises.

**2. Record what happened, not what it means.**
WODIS draws a hard line between **What You Record** (ground truth that goes in the file) and **What You Learn** (insights that apps calculate from the data). Timestamps, load, reps, RPE, superset relationships — that's What You Record. Personal records, volume trends, estimated 1RM, fatigue scores — that's What You Learn. The file stores facts. The app does math.

**3. Use what you need, ignore what you don't.**
A simple logging app can write a valid WODIS file with just a handful of fields (Level 1). A velocity-tracking lab can include per-rep barbell speed and equipment config (Level 3). Conformance levels let you pick your depth. And any field your app doesn't recognize? Preserve it on round-trip. Don't drop someone else's data.

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

That's it. Fourteen lines. A complete, valid WODIS file.

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

## What You Record vs What You Learn

WODIS stores **ground truth** — the things that disappear if you don't capture them in the moment:

- Timestamps (when each exercise and set happened)
- Load (how much weight, per set or per rep)
- Reps completed
- RPE / RIR (how hard it felt, recorded at the moment of effort)
- Superset relationships (which exercises were paired)
- Rest periods (actual measured time, not planned)
- Failure and form observations
- Assisted / partial rep flags

**Derived insights** are the app's job, not the file's:

- Personal records (1RM, volume PRs)
- Volume metrics (tonnage, sets per muscle group)
- Estimated 1RM (Epley, Brzycki)
- Fatigue and freshness context
- Progressive overload trends

The file is the source of truth. The app is the analyst. For the full breakdown, see [docs/what-you-record.md](docs/what-you-record.md).

## Conformance Levels

Not every app needs every field. WODIS defines three levels so you can pick the depth that fits:

| Level | Name | What it covers |
|---|---|---|
| **Level 1** | Minimal | The bare essentials — version, source, exercise names, timestamps, sets with reps and load. Enough to reconstruct what you did. |
| **Level 2** | Standard | Adds RPE/RIR, superset relationships, rest times, set types, muscle groups, and failure flags. What a serious training app should export. |
| **Level 3** | Rich | Per-rep atomic arrays, velocity data, equipment config, media attachments — all via `_extra`. For research tools and advanced trackers. |

For the full field list per level, see [docs/conformance.md](docs/conformance.md).

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
