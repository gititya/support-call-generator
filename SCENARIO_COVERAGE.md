# Scenario Coverage

This repo currently generates synthetic B2B SaaS support-call fixtures from curated scenario packs. It does not yet generate arbitrary B2B scenarios, B2C support calls, or industry-specific support domains.

## In Scope Now

### Permissions and access

Operational questions around user access, roles, identity changes, group membership, entitlement sync, and permission inheritance.

Current root-cause catalog includes:

- missing group role after migration
- SSO group mismatch after department change
- SCIM sync delay
- stale entitlement cache
- inherited role conflict
- direct assignment conflict
- disabled role mapping rule
- manually retained user no longer entitled

### Onboarding and migration

Operational questions around imported records, migrated roles, ownership mapping, environment mismatches, and migration scope.

Current root-cause catalog includes:

- archived team export filter
- custom legacy role mapping
- ownership translation failure
- duplicate merge
- environment mismatch
- inactive owner exclusion
- field mapping fallback
- partial export scope

### Workspace setup

Operational questions around domain verification, OAuth, integration permissions, provisioning, templates, and setup dependencies.

Current root-cause catalog includes:

- DNS record on wrong host
- declined OAuth permission
- missing integration write scope
- admin approval dependency
- connector authorization failure
- provisioning timeout
- template dependency failure
- region mismatch

### Integrations and data sync

Operational questions around connector authentication, webhook delivery, CRM sync state, field mappings, external IDs, and partial sync behavior.

Current root-cause catalog includes:

- expired OAuth refresh token
- webhook retry exhaustion
- external ID mapping conflict
- CRM field type mismatch
- rate limit backoff delay
- duplicate record merge rule
- partial sync cursor reset
- stale integration permission scope

### Billing, plan, and entitlement

Operational questions around plan state, seats, feature gates, invoice holds, usage metering, and entitlement propagation.

Current root-cause catalog includes:

- seat limit reached
- feature gate missing after plan change
- failed invoice grace period
- trial expiration entitlement lag
- usage meter delay
- invoice owner mismatch
- downgrade removed premium permission
- contracted add-on not provisioned

## Variation Within Scope

For each scenario family, the generator can vary:

- customer persona, mood, clarity, patience, and technical skill
- agent quality
- difficulty profile: simple, hard, harder
- resolution outcome: resolved, probable cause, escalated, handoff, unresolved
- wrong paths and false leads
- delayed facts
- synthetic context events/product telemetry
- irrelevant or conflicting context
- expected support state by turn
- intent tags
- consumer-facing summary
- data sensitivity / exposure marker

## Export Surfaces

The default export is for repos that need reviewed synthetic support-call transcripts and case metadata.

The realtime-support export is for repos that need transcript plus process-state fixtures:

- `exports/realtime_support_envelope.json`
- `exports/realtime_support/*.json`
- schema `support_process_fixture.v1`

The realtime export is designed for staging/import/report review before promotion into a consuming repo's source-of-truth fixtures.

## Out Of Scope Today

- arbitrary plain-English B2B scenario generation
- top-level B2B/B2C domain selection
- B2C consumer support
- industry-specific packs such as healthcare, fintech, ecommerce, insurance, travel, or logistics
- voice/audio simulation
- multilingual calls
- consumer policy adjudication

## Candidate Growth Areas

Likely next B2B packs:

- reporting or dashboard discrepancies
- performance and latency incidents
- account provisioning and deprovisioning
- notification and email delivery
- audit logs and compliance exports
- CRM, helpdesk, or data warehouse integrations
- admin policy and configuration conflicts

Each new pack should define root causes, wrong paths, delayed facts, telemetry events, and expected support-state behavior before being treated as covered.
