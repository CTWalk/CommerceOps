# Testability design

The CommerceOps automation design treats testability as a product-engineering concern rather than a collection of brittle test tricks.

## Semantic contracts

Shared semantic identifiers provide stable intent across Playwright and Appium. Where black-box mobile automation and accessibility benefit from the same semantics, user-facing ARIA labels are preferred over hidden test-only hooks.

## Deterministic state

State reset and controlled fixtures make business workflows reproducible. Determinism is setup infrastructure; it must not replace the user action or oracle that a scenario is supposed to prove.

## Observable business truth

Persisted order state and ordered domain events expose whether cross-role transitions actually occurred. This lets UI tests distinguish presentation success from business success.

## Failure diagnostics

Browser and mobile diagnostics capture useful evidence while redacting credentials, tokens, cookies, card data, and other sensitive values. Evidence is attached to failures so diagnosis starts from observable facts instead of speculative retries.

## Boundaries

Testability must not create production-unsafe bypasses. Unrestricted state mutation, bypass-auth flags, privileged debug endpoints, or shared production credentials are outside the public design.
