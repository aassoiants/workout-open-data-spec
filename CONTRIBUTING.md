# Contributing to WODIS

## How to propose changes

Open a GitHub issue first to discuss the change. Once there's agreement on the approach, submit a pull request.

## What a good PR includes

- If changing the schema: update the schema file, examples, and SPECIFICATION.md.
- If adding a new field: include a rationale for why it can't live in `_extra`.

## Versioning policy

WODIS follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **Patch** (1.0.x) — Typo fixes, clarifications. No schema changes.
- **Minor** (1.x.0) — New optional fields. Backward compatible.
- **Major** (x.0.0) — Breaking changes: removed fields, changed types, new required fields.

## Style conventions

- JSON field names in `snake_case`
- Timestamps in ISO 8601
- Weight in kilograms
- Durations in seconds

## Code of conduct

Be respectful. Focus on the work.
