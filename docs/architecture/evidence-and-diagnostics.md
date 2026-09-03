# Evidence and diagnostics

A failing automation run should answer more than “the assertion failed.”

CommerceOps evidence is designed around the boundary under test:

- browser console/page/API diagnostics for Playwright;
- screenshots, page source, native hierarchy, Logcat, package/activity state for Appium;
- device screenshot/UI hierarchy, backend state/events, Logcat, and action output for Maestro;
- deterministic screenshots and pixel/geometry checks for rendered acceptance.

Sensitive values are redacted before diagnostic attachment. Raw artifacts are retained internally when useful, but only stable, reviewed first-party evidence is selected for the public showcase.
