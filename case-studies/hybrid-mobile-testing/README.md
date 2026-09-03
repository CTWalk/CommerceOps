# Hybrid mobile testing — why Playwright, Appium, and Maestro all exist

Using three UI automation frameworks is defensible only when each proves a different boundary.

```text
browser behavior        → Playwright
hybrid/native contract  → Appium
packaged black-box UX   → Maestro
business truth          → API / persisted state
```

## Appium-owned properties

Appium is intentionally focused on boundaries Playwright cannot prove sufficiently: native/WebView context discovery, Capacitor session/cookie behavior, native HTTP bridge status/body preservation, hardware Back across SPA history, and WebView reacquisition after native navigation.

## Maestro-owned properties

Maestro owns installed-app user acceptance and lifecycle behavior: visible role journeys, keyboard interaction, orientation, background/foreground transitions, process death/session recovery, and black-box cross-role flows.

## Design rule

A framework earns its maintenance cost only when it owns a risk another cheaper layer cannot prove well enough. Scenario parity therefore means business-behavior parity where useful, not line-for-line duplication.
