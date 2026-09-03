# Layer ownership

Multiple frameworks are justified only when they contribute different evidence.

| Layer | Primary ownership | Examples of unique evidence |
| --- | --- | --- |
| API / database | business and contract truth | status/body, RBAC, persisted transitions, ordered events, deterministic reset |
| Playwright | browser regression | browser journeys, routing, responsive behavior, accessibility/semantic contracts |
| Appium | hybrid/native contract | native↔WebView context, cookie/session bridge, HTTP bridge behavior, hardware Back |
| Maestro | packaged black-box acceptance | installed-app journeys, keyboard, orientation, foreground/background, process death |
| Rendered/visual | representation truth | clipping, overlap, canvas pixels, responsive geometry, visual state |

The same business scenario may appear in more than one layer when each layer proves a different boundary. Mechanical duplication is avoided.
