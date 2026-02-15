# Event Wire Contract

Canonical envelope fields:
- `event_id` (string, required)
- `trace_id` (string, required)
- `event_type` (string, required)
- `schema_version` (string, required)
- `occurred_at` (RFC3339 string, required)
- `source` (string, required)
- `payload` (object, required)
- `attributes` (map<string, string>, optional)
