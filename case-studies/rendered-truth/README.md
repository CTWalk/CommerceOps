# Rendered truth

Correct API data or DOM structure does not prove that a user can actually see a correct, usable visual surface. Screenshot matching alone also cannot prove that the underlying business values are correct.

CommerceOps separates the oracles:

- application/bootstrap truth;
- responsive geometry and clipping/overlap;
- semantic/accessibility state;
- canvas/pixel existence where rendering itself is the property;
- API/export/state truth for the underlying values.

For the Reports surface, visual checks are cross-checked against report data rather than treating pixels as the business oracle.

Accepted examples are under `../../evidence/rendered-ui/`.
