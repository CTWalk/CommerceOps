# Deterministic state

Reliable workflow verification requires a known starting state.

CommerceOps uses explicit reset/fixture boundaries so a test can reason about inventory, cart, checkout, orders, roles, and events without depending on execution order.

Deterministic setup follows three rules:

1. Reset is observable and must fail closed when unavailable.
2. Reset is not counted as proof of the business scenario itself.
3. Tests still assert the final authoritative state rather than assuming setup or UI feedback implies success.

This separation makes failures attributable: fixture failure, environment failure, harness failure, and product failure are not collapsed into one generic red test.
