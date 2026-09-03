# CommerceOps Quality Engineering Strategy

## Principle

Use the **smallest verification layer that can authoritatively prove the risk**. Do not duplicate the same business rule across frameworks merely to increase automation count.

CommerceOps is stateful and multi-role. High-value risks therefore include state transitions, RBAC, persistence, browser integration, rendered truth, native packaging/lifecycle behavior, and cross-role workflow completion.

## Layer ownership

| Layer | What it should prove | Primary oracle |
|---|---|---|
| API / contract | HTTP state transitions, authorization, request/response contracts | HTTP semantics + returned domain state |
| Database | persistence, normalized state, cross-layer invariants | PostgreSQL rows/constraints |
| Playwright | browser journeys, semantic UI contracts, role navigation integrated with the backend | backend/API truth after browser actions plus user-visible state where wording itself matters |
| Appium | packaged mobile behavior, WebView/native integration, device-specific interaction | application state + device/runtime behavior |
| Maestro | high-value cross-role/mobile business flows and lifecycle-oriented verification | semantic UI state plus authoritative state probes where required |
| Rendered/visual | evidence that a visual surface actually rendered rather than merely exposing matching data elsewhere | pixels/geometry + accessible/API/export truth |

The exact suite composition may evolve. A framework is retained only when it contributes unique evidence economically.

## Deterministic state

Tests should own their prerequisites and must not depend on execution order or state produced by a previous scenario.

Controlled reset/fixture mechanisms are preferred over sleeps, retries, or assumptions about whatever state happens to exist.

A public test example may document its required fixture or reset contract without exposing production-only configuration.

## Selector contract

Prefer semantic contracts such as:

- `data-testid`;
- accessibility role/name;
- stable user-facing text when the wording itself is the product state being verified.

Avoid action selectors based on:

- DOM ancestry;
- generated framework attributes;
- layout/CSS implementation details;
- hard-coded pixel coordinates.

## Negative controls

A verification strategy should show that important boundaries can actually fail.

Representative examples include:

- invalid credentials remain unauthenticated;
- customer navigation to staff-only areas is blocked;
- the same customer session is rejected by the corresponding backend endpoint;
- invalid state transitions fail rather than silently succeeding.

Negative controls belong at the layer that most directly proves the boundary; Playwright or Appium should not mechanically repeat every API/domain negative test.

## Representative browser and mobile scenarios

### Access / RBAC

Compare visible navigation/workspace ownership with server-side authorization rather than assuming hidden UI equals secure authorization.

### Purchase

Drive the user journey through discovery, cart, checkout/payment review, and order placement, then verify the resulting authoritative state rather than relying on UI optimism alone.

### Refund lifecycle

Prove that Customer, Support, Supervisor, then Support own distinct transitions before the Customer sees completion.

This scenario is especially useful for demonstrating cross-role orchestration and distinguishing product failures from automation/harness failures.

## Rendered truth

Where a surface such as Reports has multiple representations—canvas, accessible data, export/API state—verification should prove both:

1. that the underlying values are truthful; and
2. that the intended rendered representation actually exists and is usable.

A matching API response alone does not prove that a chart rendered correctly.

## Failure classification

Classify a red before repair:

- **PRODUCT / CANDIDATE** — the current product violates the accepted property;
- **TEST / HARNESS** — the automation or test infrastructure is stale or incorrect;
- **ENVIRONMENT** — the candidate was not meaningfully judged;
- **UNKNOWN** — evidence is insufficient.

Do not add retries, sleeps, weaker assertions, or skips merely to recover green.

## Verification re-entry

After a failure is understood and repaired, rerun the **smallest evidence boundary invalidated by the change** rather than automatically restarting every expensive lane.

The detailed frozen-candidate verification method remains maintained in the private repository and may be exported separately as reusable public methodology.

## Public portfolio intent

Published Playwright, Appium, and Maestro material should be presented as evidence from the real CommerceOps system under test.

The public portfolio should emphasize:

```text
risk
  -> oracle choice
  -> verification layer
  -> implementation
  -> observed failure
  -> diagnosis
  -> repair / evidence re-entry
```

This is more important than maximizing the number of exposed test files.
