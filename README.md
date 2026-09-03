# CommerceOps Quality Engineering

CommerceOps is a private multi-role commerce application used as a production-scale system under test. This publication workspace contains the material intended for a public QA/SDET showcase: verification reasoning, selected engineering case studies, methodology, and first-party product evidence.

The complete application source, backend, native projects, production configuration, and release machinery are intentionally not part of the public showcase.

## What this showcase demonstrates

The focus is not framework count. It is how verification responsibility is assigned:

```text
browser behavior        → Playwright
hybrid/native contract  → Appium
packaged black-box UX   → Maestro
business/domain truth   → API / persisted state
rendered truth          → geometry / pixels / accessibility + data oracle
```

Start with:

1. `docs/system-under-test.md` — what CommerceOps is and why it is a useful SUT.
2. `docs/architecture/layer-ownership.md` — why each test layer exists.
3. `case-studies/refund-lifecycle/` — the flagship cross-role workflow.
4. `case-studies/hybrid-mobile-testing/` — Playwright/Appium/Maestro boundary design.
5. `methodology/` — how failures are classified and how verification evidence is accepted.
6. `evidence/` — verified first-party CommerceOps product scenes.

## Code exposure

Runnable automation remains authoritative in the private product repository. During public export, a reviewed subset is copied into normalized `tests/` and `testability/` paths. This directory therefore owns the public narrative and evidence, not duplicate working copies of the private regression suite.

## Evidence rule

Every image under `evidence/` must be first-party CommerceOps UI with recorded provenance. Third-party design-reference captures, raw logs, temporary screenshots, machine identifiers, secrets, and unreviewed failure artifacts do not belong here.
