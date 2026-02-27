# WODIS v1.0.0 Specification

> The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [BCP 14](https://www.rfc-editor.org/bcp/bcp14.txt) [RFC 2119] [RFC 8174] when, and only when, they appear in ALL CAPITALS.

## Table of Contents

- [1. Document Structure](#1-document-structure)
- [2. Field Reference](#2-field-reference)
  - [2.1 Meta](#21-meta)
  - [2.2 Session](#22-session)
  - [2.3 Exercise](#23-exercise)
  - [2.4 Set](#24-set)
  - [2.5 Rep](#25-rep)
- [3. The _extra Object](#3-the-_extra-object)
- [4. Conformance Levels](#4-conformance-levels)
  - [4.1 Level 1 - Minimal](#41-level-1---minimal)
  - [4.2 Level 2 - Standard](#42-level-2---standard)
  - [4.3 Level 3 - Rich](#43-level-3---rich)
  - [4.4 Round-Trip Preservation](#44-round-trip-preservation)
- [5. Versioning](#5-versioning)
- [6. Units and Formats](#6-units-and-formats)

---

## 1. Document Structure

A WODIS document is a single JSON object. It MUST contain the following three top-level properties:

| Property | Type | Description |
|----------|------|-------------|
| `wodis_version` | string | MUST be a semantic version string identifying the WODIS specification version this document conforms to. For this specification, the value MUST be `"1.0.0"`. |
| `meta` | object | MUST be a Meta object as defined in [Section 2.1](#21-meta). |
| `session` | object | MUST be a Session object as defined in [Section 2.2](#22-session). |

Additional top-level properties MAY be present. Implementations MUST preserve any additional top-level properties they do not recognize when importing and re-exporting a WODIS document.

A minimal valid WODIS document:

```json
{
  "wodis_version": "1.0.0",
  "meta": {
    "source": "my-app"
  },
  "session": {
    "started_at": "2026-02-26T07:30:00Z",
    "exercises": [
      {
        "display_name": "Squat",
        "started_at": "2026-02-26T07:32:00Z",
        "sets": [
          {
            "reps_completed": 5,
            "load_kg": 100
          }
        ]
      }
    ]
  }
}
```

---

## 2. Field Reference

### 2.1 Meta

The `meta` object describes the recording source, the athlete, and the entry method. It is the envelope around the session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | MUST | Identifier of the application or method that originally recorded this session (e.g., `"strong"`, `"hevy"`, `"manual-csv"`). Every WODIS document MUST include this field. |
| `entry_method` | string | MAY | How the data was entered. When present, the value MUST be one of: `"manual"`, `"device_sync"`, `"imported_csv"`. |
| `athlete` | string | MAY | Display name or identifier for the person who performed the workout. |
| `_extra` | object | MAY | App-specific metadata. See [Section 3](#3-the-_extra-object). |

Additional properties MAY be present on the `meta` object and MUST be preserved on round-trip.

### 2.2 Session

The `session` object represents a single workout. It is anchored by a start time and contains the exercises performed.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `started_at` | string | MUST | ISO 8601 date-time when the session began. Every WODIS document MUST include this field. |
| `ended_at` | string | MAY | ISO 8601 date-time when the session ended. |
| `location` | string | MAY | Name or description of the gym or location where the session took place. |
| `split_type` | string | MAY | Training split label for this session (e.g., `"upper_lower"`, `"push_pull_legs"`, `"full_body"`). No controlled vocabulary is defined; apps MAY use any string value. |
| `exercises` | array | MUST | Array of Exercise objects as defined in [Section 2.3](#23-exercise). MUST contain at least one element. |
| `notes` | string | MAY | Free-text notes about the session as a whole. |
| `_extra` | object | MAY | App-specific session data. See [Section 3](#3-the-_extra-object). |

Additional properties MAY be present on the `session` object and MUST be preserved on round-trip.

### 2.3 Exercise

An `exercise` object represents a single named movement performed during the session. It contains one or more sets.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | MUST | User-facing label for the exercise as shown in the source application (e.g., `"Bench Press"`, `"Barbell Row"`). |
| `started_at` | string | MUST | ISO 8601 date-time when this exercise began within the session. Exercise order within a session MUST be derived from this field; implementations MUST NOT rely on array position as the authoritative ordering. |
| `canonical_ids` | object | MAY | Key-value pairs mapping to external exercise databases. Keys SHOULD be the database name (e.g., `"wger"`, `"exercisedb"`, `"exrx"`). Values SHOULD be the identifier in that database. No specific databases are required. |
| `muscle_groups` | array of strings | SHOULD (Level 2+) | Primary muscle groups targeted by this exercise (e.g., `["chest", "triceps", "anterior_deltoid"]`). No controlled vocabulary is defined; applications bring their own terms. |
| `variation` | string | MAY | Descriptive modifier for the exercise variant performed (e.g., `"high_bar"`, `"close_grip"`, `"deficit"`, `"pause"`). |
| `sets` | array | MUST | Array of Set objects as defined in [Section 2.4](#24-set). MUST contain at least one element. |
| `notes` | string | MAY | Free-text notes about this exercise. |
| `_extra` | object | MAY | App-specific exercise data. See [Section 3](#3-the-_extra-object). |

Additional properties MAY be present on the `exercise` object and MUST be preserved on round-trip.

### 2.4 Set

A `set` object represents a group of repetitions performed without meaningful rest. If the lifter rested, it is a new set. If the lifter changed the load and continued without rest (e.g., a dropset), it is the same set with per-rep data in the `reps` array.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reps_completed` | integer | MUST | Total number of repetitions completed in this set. MUST be an integer greater than or equal to 0. A value of `0` indicates a failed attempt where no reps were completed (e.g., an unsuccessful 1RM attempt). |
| `load_kg` | number | MUST | Weight in kilograms used for this set. A value of `0` indicates bodyweight with no external load. A negative value indicates assisted weight (e.g., `-15` means 15 kg of machine assistance on a pull-up). When the `reps` array is present with per-rep loads, this field SHOULD reflect the primary or starting load of the set. |
| `reps` | array | MAY | Per-rep atomic data. When present, each element MUST be a Rep object as defined in [Section 2.5](#25-rep). Each element represents one repetition in the order performed. The length of this array SHOULD equal `reps_completed`, but implementations MUST NOT reject documents where they differ. |
| `set_type` | string | SHOULD (Level 2+) | Classification of this set's purpose. When present, the value MUST be one of: `"working"`, `"warmup"`, `"dropset"`, `"failure"`, `"backoff"`, `"amrap"`. |
| `rpe` | number | MAY | Rate of Perceived Exertion on the Borg CR-10 scale. When present, the value MUST be in the range 1 to 10, inclusive. This is a subjective measure recorded at the moment of effort. |
| `rir` | number | MAY | Reps In Reserve: the lifter's estimate of how many additional reps could have been performed. When present, the value MUST be in the range 0 to 5, inclusive. |
| `rest_seconds_actual` | number | SHOULD (Level 2+) | Actual time in seconds the lifter rested before beginning this set. This is ground truth (the rest that was actually taken), not a derived value from timestamp math. MUST be greater than or equal to 0 when present. |
| `is_failure` | boolean | MAY | `true` if the set was taken to muscular failure (the lifter could not complete another rep with acceptable form). |
| `form_flags` | array of strings | MAY | Observed technique deviations during the set (e.g., `["hip_shift", "shortened_rom", "excessive_lean"]`). No controlled vocabulary is defined. |
| `superset_id` | string | SHOULD (when applicable) | Identifier grouping sets that are performed as part of the same superset. All sets sharing a `superset_id` across any exercise in the session are part of the same superset. This is intentional structure and MUST NOT be inferred from timing alone. |
| `superset_sequence` | integer | MAY | Position of this set's exercise within the superset rotation (e.g., `1` for the first exercise, `2` for the second). When present, MUST be a positive integer. |
| `transition_time_seconds` | number | MAY | Time in seconds to move between exercises within a superset. MUST be greater than or equal to 0 when present. |
| `timestamp` | string | RECOMMENDED | ISO 8601 date-time when this individual set was performed. RECOMMENDED for all implementations; enables per-set rest period derivation and fine-grained session analysis. |
| `notes` | string | MAY | Free-text notes about this set. |
| `_extra` | object | MAY | App-specific set data. See [Section 3](#3-the-_extra-object). |

Additional properties MAY be present on the `set` object and MUST be preserved on round-trip.

### 2.5 Rep

A `rep` object is the atomic unit of WODIS. It represents a single repetition and captures data that can vary from one rep to the next within the same set, most commonly load changes (dropsets) and assistance (spotter on final reps).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `load_kg` | number | MUST | Weight in kilograms for this specific repetition. This allows load to vary within a set (e.g., a dropset where weight decreases mid-set). Follows the same conventions as the set-level `load_kg`: `0` for bodyweight, negative for assisted. |
| `assisted` | boolean | MAY | `true` if this rep was performed with external assistance (e.g., spotter help, machine counterbalance). Defaults to `false` when absent. |
| `partial` | boolean | MAY | `true` if this rep used an incomplete range of motion (intentional or due to fatigue). Defaults to `false` when absent. |
| `completed` | boolean | MAY | `true` if the rep was successfully finished through the intended range of motion. `false` indicates a failed rep attempt. Defaults to `true` when absent. |
| `_extra` | object | MAY | App-specific rep data. See [Section 3](#3-the-_extra-object). |

Additional properties MAY be present on the `rep` object and MUST be preserved on round-trip.

---

## 3. The `_extra` Object

The `_extra` property is the extension mechanism for WODIS, following the same design principle as GPX's `<extensions>` element.

### Rules

1. **Availability.** Every object in a WODIS document (`meta`, `session`, `exercise`, `set`, `rep`) MUST support an `_extra` property. Implementations MUST NOT reject a document because `_extra` is present at any level.

2. **Round-trip preservation.** Implementations that import and re-export WODIS documents MUST preserve all `_extra` data, including data they do not recognize. An application that reads a field it does not understand MUST write it back unchanged.

3. **Namespacing.** Extensions SHOULD be namespaced by application name to avoid collisions between different apps writing to the same `_extra` object:

   ```json
   "_extra": {
     "velocityapp": { "mean_velocity_ms": 0.65 },
     "coachingapp": { "coach_note": "Good lockout" }
   }
   ```

4. **No validation.** The WODIS specification does NOT validate `_extra` contents. The `_extra` object is open and accepts any valid JSON. Validation of extension data is the responsibility of the application that produced it.

5. **Type.** When present, `_extra` MUST be a JSON object (not an array, string, or other type).

---

## 4. Conformance Levels

WODIS defines three conformance levels. Each level is a superset of the previous one. Applications SHOULD declare which level they target, and consumers SHOULD accept documents at any level.

### 4.1 Level 1 - Minimal

A Level 1 document contains the bare essentials: enough to reconstruct what exercises were performed, when, with how much weight, and for how many reps.

A conforming Level 1 document MUST include all of the following fields:

| # | Field | Location |
|---|-------|----------|
| 1 | `wodis_version` | root |
| 2 | `meta.source` | meta |
| 3 | `session.started_at` | session |
| 4 | `exercise.display_name` | exercise |
| 5 | `exercise.started_at` | exercise |
| 6 | `set.reps_completed` | set |
| 7 | `set.load_kg` | set |

Any additional fields MAY be present. Level 1 documents are what a simple logging application exports.

### 4.2 Level 2 - Standard

A Level 2 document adds the fields needed to analyze training quality: intensity, effort, structure, and recovery context.

A conforming Level 2 document MUST include all Level 1 fields and SHOULD include all of the following:

| Field | Location | Purpose |
|-------|----------|---------|
| `set_type` | set | Classifies the set's purpose (working, warmup, dropset, failure, backoff, amrap). |
| `rpe` | set | Subjective effort rating (1-10). |
| `rir` | set | Estimated reps left in reserve (0-5). |
| `rest_seconds_actual` | set | Actual rest taken before this set, in seconds. |
| `is_failure` | set | Whether the set reached muscular failure. |
| `form_flags` | set | Observed technique deviations. |
| `superset_id` | set | Groups sets performed as a superset. |
| `superset_sequence` | set | Position within the superset. |
| `muscle_groups` | exercise | Primary muscles targeted by the exercise. |

An application targeting Level 2 conformance SHOULD populate these fields whenever the data is available. Fields MAY be omitted when the data is not applicable (e.g., `superset_id` when no superset was performed).

### 4.3 Level 3 - Rich

A Level 3 document provides full per-rep atomic data and uses `_extra` for app-specific extensions: velocity tracking, tempo prescriptions, equipment configuration, and media attachments.

A conforming Level 3 document MUST include all Level 1 fields, SHOULD include all Level 2 fields, and additionally:

| Field | Location | Purpose |
|-------|----------|---------|
| `reps` | set | Per-rep atomic array. Each element is a Rep object with its own `load_kg` and OPTIONAL `assisted`, `partial`, and `completed` flags. |
| `_extra` | any level | App-specific extension data (velocity, tempo, equipment config, recovery metrics, media). |

Per-rep velocity, eccentric tempo, cable height, bar type, video attachments: all live in `_extra` at the appropriate level.

### 4.4 Round-Trip Preservation

Regardless of conformance level: if an implementation imports a WODIS document containing fields it does not recognize, it MUST preserve those fields on export. A Level 1 application that reads a Level 3 document MUST NOT strip the Level 3 data.

This rule applies to:
- Standard fields from higher conformance levels that the implementation does not use.
- All `_extra` data at every level.
- Any additional properties on any object.

---

## 5. Versioning

1. The `wodis_version` field MUST be present in every WODIS document.

2. The value MUST be a [semantic version](https://semver.org/) string in the format `MAJOR.MINOR.PATCH` (e.g., `"1.0.0"`).

3. Implementations SHOULD accept documents with a `wodis_version` they recognize and SHOULD reject or warn about versions they do not recognize.

4. **Minor versions** (e.g., `1.0.0` to `1.1.0`): New OPTIONAL fields MAY be added. Existing field types and semantics MUST NOT change. Documents conforming to an earlier minor version MUST remain valid under the new minor version.

5. **Major versions** (e.g., `1.x.x` to `2.0.0`): REQUIRED fields MAY be added, removed, or have their types changed. Major version bumps signal breaking changes that may require implementation updates.

6. **Patch versions** (e.g., `1.0.0` to `1.0.1`): Reserved for specification clarifications and errata. No schema changes.

---

## 6. Units and Formats

| Category | Rule |
|----------|------|
| **Weight** | All weight values (`load_kg` at set and rep level) MUST be in kilograms. Applications that display pounds MUST convert to kilograms for storage and interchange. |
| **Timestamps** | All timestamp fields (`started_at`, `ended_at`, `timestamp`) MUST be in [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) date-time format (e.g., `"2026-02-26T07:30:00Z"`). Timezone offset or UTC (`Z`) SHOULD be included. |
| **Durations** | All duration fields (`rest_seconds_actual`, `transition_time_seconds`) MUST be in seconds. Values MUST be numbers (integer or floating-point) and MUST be greater than or equal to 0. |
| **Field names** | All field names defined by this specification MUST be `snake_case`. Extension fields within `_extra` SHOULD follow `snake_case` but this is not enforced. |
| **Encoding** | WODIS documents MUST be encoded as UTF-8. |
| **MIME type** | The RECOMMENDED media type for WODIS documents is `application/json`. The RECOMMENDED file extension is `.wodis.json`. |
