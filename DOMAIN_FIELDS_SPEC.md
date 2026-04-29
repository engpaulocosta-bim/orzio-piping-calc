# Domain Fields Spec

## Application

- `name`
- `version`
- `recent_projects`
- `settings`

## Project

- `project_id`
- `name`
- `client`
- `site`
- `revision`
- `created_at`
- `updated_at`
- `routes`

## Route / Trace

- `route_id`
- `name`
- `description`
- `lines`

## Line Segment

- `line_id`
- `tag`
- `line_input`
- `hydraulic_cases`
- `last_report_context`
- `validation_state`

## Hydraulic Case

- `case_id`
- `name`
- `operation_mode`
- `status`
- `created_at`
- `report_context`

## Material Spec

- `family`
- `grade`
- `region`
- `dimensional_catalog`
- `roughness_m`
- `temperature_min_c`
- `temperature_max_c`
- `pressure_rating_bar`
- `service_allowlist`
- `limitations`

## Fitting Set / Valve Set

- `items`
- `source`
- `warnings`

## Report

- `report_id`
- `line_id`
- `generated_at`
- `format`
- `path`

## Validation State

- `status`
- `errors`
- `warnings`
- `dataset_missing`
- `out_of_scope`
