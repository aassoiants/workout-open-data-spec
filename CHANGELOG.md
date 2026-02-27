# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-27

### Added
- Initial WODIS v1.0.0 specification
- JSON Schema (draft-07)
- SPECIFICATION.md formal reference with ground truth vs derived data guide (Section 7)
- README with philosophy, conformance levels, extensions guide
- `load_unit` field on session (`"kg"` or `"lbs"`) - weight unit declared once per file
- Example files: minimal (kg), standard (lbs), advanced (kg)
- Schema validation test script
- Contributing guidelines (inline in README)

### Changed
- `load_kg` renamed to `load` across spec, schema, and examples (unit-agnostic, interpreted per `load_unit`)

### Removed
- No exercise database bundled (format only, apps bring their own)
