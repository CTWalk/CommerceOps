# Refund lifecycle — one workflow, complementary evidence

## Risk

A refund can look successful at one screen while persisted order state, role ownership, event history, or the final customer receipt is wrong.

The workflow crosses Customer → Support → Supervisor → Support → Customer.

## Verification design

- **Playwright** drives the complete browser workflow, checks intermediate UI state, reads backend truth, and verifies the exact handoff sequence.
- **Appium** proves corresponding behavior through the packaged hybrid application and captures native/WebView evidence.
- **Maestro** performs black-box packaged-app acceptance using semantic UI actions while backend probes confirm persisted checkpoints.
- **API** owns direct workflow/state contract assertions beneath the UI layers.

A toast is never sufficient proof of refund completion.

## Failure lesson

The final customer receipt once failed in Maestro after the underlying refund had completed correctly. Evidence isolated a harness/viewport interaction problem rather than a business failure. The repair targeted navigation/anchoring and preserved the final receipt assertion instead of adding arbitrary sleeps or weakening the oracle.

See `workflow.md` and the accepted screenshots in `../../evidence/refund-lifecycle/`.
