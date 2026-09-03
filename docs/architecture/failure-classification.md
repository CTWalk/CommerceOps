# Failure classification

A red test does not identify its owner by itself.

CommerceOps uses four practical classes:

| Class | Meaning | Effect |
| --- | --- | --- |
| PRODUCT | product behavior violates the accepted contract | blocks product acceptance |
| HARNESS | test automation or testability mechanism is wrong | blocks that evidence path until repaired |
| ENVIRONMENT | execution conditions invalidate the run | voids the run; not a product defect by itself |
| UNKNOWN | evidence is insufficient to assign ownership | blocks until classified or explicitly accepted |

The repair should target the owning layer. After repair, re-enter the smallest evidence boundary invalidated by that change while respecting any stricter acceptance contract that explicitly requires broader repetition.
