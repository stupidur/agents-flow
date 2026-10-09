---
description: "Required browser and responsive visual testing matrix for frontend work, including Safari, Chrome, desktop, tablet, and mobile widths."
globs:
  - "**/*.html"
  - "**/*.liquid"
  - "**/*.css"
  - "**/*.scss"
  - "**/*.js"
  - "**/*.ts"
  - "**/*.jsx"
  - "**/*.tsx"
  - "templates/**/*.json"
alwaysApply: false
---

# Browser And Responsive Testing Rules

Apply this rule to every user-facing frontend change, including layout, styles,
responsive behavior, navigation, forms, media, animation, and interactive
components.

## Supported Browsers

- **MUST** test against the latest stable Safari and latest stable Chrome
  available in the approved test environment.
- **MUST** report the actual Safari and Chrome versions used for each test run.
- **MUST NOT** claim Safari compatibility from Chromium or Playwright WebKit
  emulation alone. Use current Safari on macOS and BrowserStack Safari on the
  required iPhone profile.
- **MUST NOT** claim complete cross-browser testing when a required browser,
  device, or viewport was unavailable. Report the missing coverage explicitly.

## Mandatory Viewport Widths

Treat these as CSS viewport widths. Use enough viewport height to inspect the
initial viewport and capture a full-page screenshot where practical.

| Class | Required width | Baseline |
| --- | ---: | --- |
| Desktop | `1920px` | MacBook Pro |
| Tablet | `768px` | Simulated tablet on MacBook Pro |
| Mobile | `390px` | iPhone 17 baseline |

Do not replace these required widths with nearby presets such as `1440px`,
`820px`, `393px`, or `375px`. Additional breakpoint-edge tests are encouraged
when the project uses breakpoints near the changed layout.

## Required Test Matrix

### Safari

1. macOS Safari at `1920px` viewport width.
2. macOS Safari responsive/simulated tablet at `768px` viewport width.
3. BrowserStack iPhone 17 using Safari at the device's `390px` CSS viewport
   baseline.

### Chrome

1. macOS Chrome at `1920px` viewport width.
2. macOS Chrome responsive/simulated tablet at `768px` viewport width.
3. macOS Chrome responsive/simulated mobile at `390px` viewport width.

## What Must Be Tested

At every required browser/viewport combination affected by the change:

- **MUST** verify there is no horizontal overflow, clipped text, unintended
  wrapping, overlap, layout shift, or content outside its container.
- **MUST** verify typography, spacing, colors, images, icons, borders, and
  alignment against the approved design or requirement.
- **MUST** verify header, navigation, drawers, modals, forms, buttons, links,
  carousels, accordions, tabs, and sticky elements that intersect the changed
  flow.
- **MUST** verify pointer and keyboard interaction on desktop and touch behavior
  on the BrowserStack mobile device where relevant.
- **MUST** verify focus visibility, reduced-motion behavior, image loading,
  responsive image selection, and meaningful content at browser zoom when the
  change can affect them.
- **MUST** verify loading, empty, error, disabled, selected, expanded, and other
  task-relevant states rather than testing only the default state.
- **MUST** inspect browser console errors and failed network requests introduced
  by the change.

## Evidence And Reporting

- **MUST** record the tested URL or template, browser name and version, device or
  viewport width, and pass/fail result.
- **MUST** capture screenshots for changed visual areas at `1920px`, `768px`,
  and `390px`; retain them in an ignored local output directory unless the user
  explicitly requests committed evidence.
- **MUST** identify whether the mobile Safari result came from BrowserStack
  iPhone 17 or another environment.
- **MUST** report any untested matrix entry and the remaining compatibility risk.
- **MUST NOT** upload, publish, or modify a remote theme merely to obtain a test
  URL without explicit user approval for that exact Shopify operation.

## Completion Gate

Frontend work is not fully verified until all applicable matrix entries pass.
When access to Safari, BrowserStack, a preview URL, or the target store is
missing, local checks may continue, but the final report must say verification
is partial and list the outstanding entries.
