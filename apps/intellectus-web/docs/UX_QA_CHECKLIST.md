# Guided diagnostic UX and accessibility QA

## Automated coverage

- Shared protection and setup message for steps 2–5 without a result.
- Disabled future progress steps until their prerequisites exist.
- Required field, website, country and inclusive research-window validation.
- First-invalid-field focus after form submission.
- ISO country code storage and human-readable brief label.
- Supporting-document type, size, count, removal and reset behavior.
- Funding, impact, operations and neutral local scenarios.
- Agenda selection, custom questions, one consultant note and brief derivation.
- Draft/Ready state, conditional workshop panel, Calendar URL and print action.
- Automated axe checks on each of the five rendered steps. Colour contrast is
  disabled in jsdom because it requires browser layout and remains manual QA.
- Runtime guardrails for prohibited copy, retired routes, network access and
  browser persistence.

Automated checks do not establish full WCAG conformance or user comprehension.

## Manual browser QA still required

- Review 320, 375, 768, 1024 and 1440 px widths.
- Confirm no horizontal viewport scrolling.
- Complete the five-step flow with keyboard only.
- Confirm route-change focus and skip-link behavior in Chrome and VoiceOver.
- Inspect native details markers and checkbox state.
- Check the native country and date controls across supported browsers.
- Inspect print preview, pagination and PDF output on macOS and Windows.
- Confirm the generated Calendar event dates in the user's actual timezone.
- Confirm external-tab behavior and review the generated Calendar description.
- Validate line length, action hierarchy and visual density with real content.
- Run a focused comprehension test with first-time consultant users.
