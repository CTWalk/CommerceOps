# Frozen-candidate verification

High-confidence verification needs a stable subject.

## Candidate contract

Before a gate begins, record the candidate revision and the relevant environment/toolchain assumptions. The test execution must not silently rebuild or mutate the candidate in a way that changes the thing being accepted.

## Re-entry

When a failure is repaired, distinguish product changes from harness/environment changes. A product change creates a new candidate. A harness-only repair may preserve already-proven product behavior but must re-run the invalidated evidence path.

## Evidence

Retain the exact command/suite identity, candidate identity, result, and diagnostic artifacts needed to classify failures. Negative controls are useful where they prove that an oracle can actually detect the targeted defect instead of merely returning green.
