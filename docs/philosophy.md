# WODIS Design Philosophy

> The key words "MUST", "MUST NOT", "SHOULD", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

This document explains **why** WODIS makes the design choices it does. It is not a reference for the schema or field definitions — for that, see the [JSON Schema](../wodis.schema.json) and the [conformance levels](conformance.md). This is the thinking behind the spec, for people who want to understand the reasoning before they build on it.

---

## Why JSON, Not Binary

WODIS files are plain JSON. Not Protocol Buffers, not FIT, not CBOR, not XML.

The deciding factor is longevity. A `.wodis` file MUST be something you can open in any text editor in 2040 and still understand what happened in your workout. Binary formats fail this test. Garmin's FIT format requires an SDK just to decode a set of bench press reps. If Garmin disappears or stops maintaining the SDK, your data becomes an opaque blob. JSON has no SDK. It has curly braces.

XML would also work for human readability, but it is excessively verbose for the kind of data WODIS stores. A single set in XML takes 8-10 lines of angle brackets to express what JSON does in 3. When a serious lifter has 5,000+ sessions, verbosity becomes a real storage and parsing cost.

JSON hits the sweet spot:

- **Human-readable.** Open it, read it, understand it. No decoder ring required.
- **Machine-parseable.** Every programming language ships with a JSON parser. No dependencies.
- **Compact enough.** Not as small as binary, but small enough that compression (gzip) closes the gap when it matters.
- **Universally supported.** Python, JavaScript, Go, Rust, Swift, Kotlin, Excel (via Power Query), even bash (`jq`). There is no platform that cannot read JSON.

A WODIS file SHOULD be valid JSON that passes `JSON.parse()` without modification. No comments, no trailing commas, no extensions. Strict JSON means maximum compatibility.

---

## Why the Rep Is the Atom

Most workout apps treat the **set** as the smallest unit. WODIS treats the **rep** as the smallest unit. This is a deliberate choice driven by a specific problem.

### The Dropset Problem

You are doing bench press. You complete 8 reps at 100 kg. Without reracking, your partner pulls a plate and you grind out 4 more reps at 80 kg. The last rep at 80 kg, your spotter gives you a nudge — it is assisted.

In a set-atomic model, you have to choose:

- Record it as one set: `{ reps: 12, load_kg: ??? }` — What load do you put? 100? 80? An average? You have already lost data.
- Record it as two sets: `{ reps: 8, load_kg: 100 }` and `{ reps: 4, load_kg: 80 }` — But they were not two sets. There was no rest. The second "set" only makes sense in the context of the first. And you still lost the assisted flag on rep 12.

In a rep-atomic model, the truth is preserved:

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

Every rep carries its own load, its own flags, its own truth. Nothing is lost.

### Most Apps Won't Use This

And that is fine. The per-rep `reps[]` array is OPTIONAL. A simple logging app writes `reps_completed` and `load_kg` at the set level and calls it a day — that is a valid Level 1 file. But the spec MUST support per-rep data because ground truth matters. When someone does need it — a coach reviewing form breakdown, a researcher tracking velocity per rep, a lifter who got spotted on rep 9 — the data model is already there. You do not have to retrofit atomicity after the fact.

The hierarchy is clear: sessions contain exercises, exercises contain sets, sets contain reps. The rep is the atom. Everything else is a container.

---

## Why Timestamps, Not Sequence Numbers

Exercises in a WODIS file are ordered by their `started_at` timestamps. There is no `sequence` or `order` field. This is intentional.

### The Contradiction Problem

If you store both a sequence number and a timestamp, you create two sources of truth for the same fact: "which exercise came first." Eventually they will disagree. An app might reorder exercises in the UI (sequence changes) without updating timestamps, or merge two sessions where timestamps interleave but sequences don't. Now you have a file that says exercise 2 happened before exercise 1 according to timestamps, but exercise 1 is listed as sequence 1. Which is correct?

WODIS avoids this by having a single source of truth: timestamps. Exercise order is derived from `started_at`. If you need to display exercises in order, sort by timestamp. If two exercises share the same timestamp (supersets), use `superset_id` to express the relationship explicitly rather than overloading sequence numbers.

### Timestamps Carry More Information

A sequence number tells you "this was third." A timestamp tells you "this started at 07:45:12Z." From the timestamp, an app can derive:

- Exercise order (sort)
- Rest periods between exercises (diff between one exercise's last set and the next exercise's `started_at`)
- Session duration (first `started_at` to last activity)
- Time of day patterns (morning vs evening training)

Sequence gives you one of those. Timestamps give you all of them. Store the richer data; derive the simpler view.

Exercises MUST include a `started_at` timestamp. Sets SHOULD include a `timestamp` field when the recording app has that information. The more temporal data in the file, the more an app can reconstruct about what actually happened.

---

## Why `_extra`, Not More Fields

Every object in WODIS — metadata, session, exercise, set — has an `_extra` field. This is a freeform JSON object where apps can put whatever they want. It is the single most important design decision in the spec.

### The GPX Lesson

GPX (GPS Exchange Format) was created in 2004. It is still the universal standard for GPS tracks in 2026 — over 20 years later. One of the key reasons is its `<extensions>` tag. When Garmin wanted to add heart rate data, they did not need to change the GPX spec. They put it in extensions. When Strava wanted to add power data, same thing. The core spec stayed simple and stable. Innovation happened at the edges.

WODIS follows the same pattern. The core schema defines the fields that every workout app needs: exercise names, sets, reps, load, timestamps, RPE. These are the universal primitives of strength training. They MUST NOT change frequently, because stability is what makes a spec adoptable.

But the world of strength training is vast:

- Velocity-based training apps want mean concentric velocity per rep.
- Tempo apps want eccentric/pause/concentric/pause timing.
- Equipment-aware apps want cable height, bar type, bench angle.
- Recovery platforms want Whoop strain, Oura readiness, HRV.
- Coaching platforms want program context (mesocycle week, training block name).

If we added every possible field to the core schema, two things would happen:

1. **The spec would be too complex to implement.** A simple logging app would face a 200-field schema and give up.
2. **The spec would never stabilize.** Every new device or methodology would require a schema revision.

Instead, the core stays minimal and `_extra` handles the rest. Three rules govern its use:

1. **Apps MUST preserve `_extra` on round-trip.** If you import a file with `_extra` data you don't recognize, you MUST write it back out when exporting. Never drop someone else's data.
2. **Apps SHOULD namespace their extensions.** Use `"_extra": { "myapp": { ... } }` to avoid collisions between different apps writing to the same `_extra` object.
3. **The spec does not validate `_extra` contents.** It is an open object. Anything goes. Validation is the responsibility of the app that wrote it.

This means WODIS can support use cases that do not exist yet. The spec does not need to predict the future; it just needs to leave room for it.

---

## Why No Exercise Database

WODIS does not include a taxonomy or database of exercises. There is no canonical list of exercise names, no exercise IDs, no muscle group mappings baked into the spec. This is a deliberate omission, not an oversight.

### The Licensing Trap

The most comprehensive open exercise database is wger's, which is licensed under CC BY-SA 3.0. That is a copyleft license — any derivative work MUST also be CC BY-SA. If WODIS bundled or depended on that database, every app using WODIS would inherit the CC BY-SA obligation. An MIT-licensed spec that requires a CC BY-SA dependency is a licensing contradiction that would scare away commercial adopters.

### The Naming Problem

There is no consensus on exercise names. Consider the squat:

- "Squat" vs "Back Squat" vs "Barbell Back Squat"
- "High Bar Squat" vs "High Bar Back Squat"
- Strong calls it "Barbell Squat." Hevy calls it "Squat (Barbell)." JEFIT calls it "Barbell Full Squat."
- In German it is "Kniebeuge." In Japanese it is "squat" transliterated to katakana.

A spec that mandates exercise names will be wrong for half its users and annoying for the other half. Exercise naming is a UI concern, not an interchange concern.

### The Tar Pit

Exercises have infinite variations. Is a close-grip bench press a separate exercise or a variation of bench press? What about a floor press? A pin press? A Spoto press? A Larsen press? Every fitness app has made different decisions about this taxonomy, and none of them agree. Trying to unify exercise semantics across all apps is a tar pit that would consume the spec's entire maintenance budget.

### What WODIS Does Instead

WODIS standardizes **workout structure**, not exercise semantics. The spec gives you:

- `display_name` — Whatever the user or app calls the exercise. Free text, no constraints.
- `canonical_ids` — An OPTIONAL object where apps MAY include references to external databases: `{ "wger": 42, "exercisedb": "0025", "myapp": "bench-press-flat" }`. This lets apps map to their own taxonomies without the spec picking a winner.
- `muscle_groups` — An OPTIONAL array for apps that want to tag muscles. The spec does not define the allowed values; apps bring their own vocabulary.
- `variation` — An OPTIONAL free-text field for descriptors like "high_bar", "close_grip", "deficit".

Apps bring their own exercise lists. The spec provides the hooks (`canonical_ids`) for apps to cross-reference without mandating a single source of truth for exercise identity.

---

## Prior Art

WODIS did not emerge in a vacuum. We studied what exists, learned from what works, and identified what is missing.

### OpenWeight

[openweight.dev](https://openweight.dev) — Apache 2.0 licensed.

The closest prior art to WODIS. OpenWeight covers sets, RPE, supersets, and tempo. It is a well-designed spec by someone who clearly understands the problem space. WODIS differs in two key areas: per-rep atomicity (OpenWeight's smallest unit is the set, so it has the dropset problem described above) and the explicit separation of recorded ground truth from derived insights.

### wger

A rich open-source workout manager with a thoughtful data model that handles supersets, dropsets, RIR, and progressive overload. But wger is an **application API**, not a portable interchange specification. Its data model is optimized for its own database schema, not for moving data between arbitrary apps. You cannot hand a wger API response to a different app and expect it to understand the structure without wger-specific knowledge.

### Garmin FIT

The FIT protocol includes `SetMesg` with fields for reps, weight, and set type. It is technically capable of recording strength data. In practice, it is a proprietary binary format that is poorly documented for strength training use cases, requires the FIT SDK to decode, and is designed primarily for Garmin's ecosystem. It solves the cardio interchange problem well. It does not solve the strength training interchange problem.

### GPX

GPX is the inspiration for WODIS's overall approach. Created in 2004, GPX proved that a format can achieve universal adoption if it gets three things right: simplicity (small core schema), extensibility (the `<extensions>` tag), and human readability (plain XML you can open in Notepad). GPX is still the standard for GPS tracks 20+ years later. WODIS aims to do for the barbell what GPX did for the trail.

### Hevy and Strong CSV Exports

The de facto "standard" for workout data portability is the CSV export from apps like Hevy and Strong. These exports are proprietary and lossy: they flatten supersets into disconnected rows, drop RPE, discard rest times, and lose exercise ordering context. They work for simple "what did I lift" queries but fail for anything that requires structural fidelity. WODIS exists because CSV is not good enough.

---

## Summary

| Decision | Reasoning |
|---|---|
| JSON format | Human-readable in 2040, no SDK required, universal parser support |
| Rep as atom | Dropsets, assisted reps, and partial reps need per-rep granularity |
| Timestamps over sequence | Single source of truth, richer data, no contradiction risk |
| `_extra` over more fields | Core stays stable and simple; innovation happens at the edges |
| No exercise database | Licensing risk, naming disagreements, infinite taxonomy — not our problem |
