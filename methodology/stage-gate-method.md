# Stage-gate verification method

CommerceOps uses stage gates to keep candidate acceptance attributable.

## Core sequence

1. Freeze the candidate identity and scope.
2. Confirm environment and fixture preconditions.
3. Map each acceptance property to an owning verification layer and oracle.
4. Execute the required gate without mutating the candidate under test.
5. Retain enough evidence to classify every red.
6. Classify failures as PRODUCT, HARNESS, ENVIRONMENT, or UNKNOWN.
7. Repair only the owning layer and record whether the candidate changed.
8. Re-enter the invalidated evidence boundary.
9. Stop when the acceptance contract is satisfied and no live uncertainty remains.

A gate is evidence about a particular candidate under known conditions, not a generic badge that can be transferred between unrelated revisions.
