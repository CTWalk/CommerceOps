# Verification model

CommerceOps verification starts from risk, not tooling.

For each property under test:

```text
risk
→ observable property
→ cheapest authoritative layer
→ oracle
→ evidence
→ failure classification
→ re-entry boundary
```

## Oracle hierarchy

A visible success message is evidence of UI feedback, not automatically evidence of business completion. The authoritative oracle depends on the property:

- UI wording or affordance → rendered/semantic UI assertion;
- role authorization → route/API denial plus authenticated role truth;
- workflow transition → persisted state and ordered domain events;
- native integration → packaged-app/native-WebView behavior;
- visual existence/layout → geometry or pixel evidence;
- API contract → status, body, schema, and state transition.

## Layer rule

Use the smallest layer that can prove the property without losing the failure mode being investigated. Higher-cost UI automation is justified only when lower layers cannot observe the required boundary.

## Evidence rule

A green result is meaningful only when the run had valid preconditions, used the intended candidate, and exercised the required oracle. Missing infrastructure is not green coverage; a harness defect is not automatically a product defect.
