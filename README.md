# CommerceOps Quality Engineering — public export branch

This is an **orphan staging branch** used to assemble the curated public CommerceOps QA/SDET portfolio.

It is intentionally independent from the private `Shooting_App` Git history. The branch exists so reviewed public material can be prepared and inspected without exposing the private application's ancestry, implementation, release configuration, credentials, or unrelated repository history.

## What belongs here

Only material explicitly approved for public exposure, such as:

- QA/SDET portfolio documentation and methodology;
- selected Playwright, Appium, Maestro, API, and supporting test code;
- selected testability examples;
- first-party CommerceOps evidence with verified provenance.

## What this branch is not

- It is **not** the CommerceOps product or App Store release source of truth.
- It is **not** a development branch for the private application.
- It must never receive a merge from private `main`.
- It must not contain private release/signing material, secrets, raw private diagnostics, or unreviewed source files.

The private `Shooting_App/main` branch remains the authoritative product and release repository. This branch is disposable publication staging whose contents may later be pushed to the public CommerceOps repository after review.
