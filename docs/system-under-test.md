# System Under Test

CommerceOps is a multi-role commerce application used as the real system under test for the quality-engineering material selected for public publication.

The complete application source remains private. Public screenshots, workflow descriptions, and selected supporting code provide only the context necessary to understand the published automation and verification decisions.

## Roles

CommerceOps contains four primary workspaces:

- **Customer** — shopping, cart, checkout, order history, refund requests, profile/help and related customer journeys.
- **Support** — customer/order support and refund handling.
- **Supervisor** — approval responsibilities in controlled workflows such as refunds.
- **Operations** — inventory, fulfillment, reports, and audit-oriented work.

The value of the system as a test target comes from state moving across these roles rather than from isolated CRUD screens.

## Representative workflows

### Purchase

```text
Customer
  -> product discovery
  -> variant/availability decision
  -> cart
  -> checkout/payment review
  -> order
```

Automation should not treat a success toast or navigation alone as authoritative proof. Where appropriate, the resulting backend/database state is used as the oracle.

### Refund lifecycle

```text
Customer request
  -> Support review/escalation
  -> Supervisor approval
  -> Support completion
  -> Customer final receipt
```

This workflow is useful for demonstrating:

- cross-role authorization;
- state-transition ownership;
- browser/mobile orchestration;
- backend truth versus visible UI truth;
- diagnosis of harness failures without weakening product assertions.

### Operations

Representative risks include:

- inventory availability and persistence;
- fulfillment recovery;
- reports/export truth;
- authorization boundaries between customer and staff workspaces.

## Testability characteristics

The real application includes engineering seams intentionally useful for deterministic verification, including semantic identifiers, controlled state/reset mechanisms, backend/API observability, role-aware workflows, and native packaging/lifecycle behavior.

Selected examples may be published when they materially explain the QA design. Their presence in the public showcase does not imply that the full application implementation is public.

## Screenshot policy

First-party screenshots from the private CommerceOps application may be published as **system-under-test evidence**.

They must be described as screenshots of the real application being verified, not as proof that the application source is present in the public repository.

Do not publish screenshots containing:

- secrets or credentials;
- private/local filesystem paths;
- device identifiers;
- debug overlays that expose private configuration;
- third-party reference applications or assets without redistribution rights.
