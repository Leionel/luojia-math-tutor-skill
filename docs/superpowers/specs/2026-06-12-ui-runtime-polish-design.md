# UI Runtime Polish Design

## Goal

Fix the four runtime issues observed in the chat workspace without changing
the API contract or adding frontend dependencies:

1. Unassessed radar axes must not look like real 15% scores.
2. Mode descriptions must not cover chat content on touch-sized screens.
3. Large session histories must not render every row at once.
4. Mastery trend must compare the previous assessment with the current one and
   remain stable after a page refresh.

## Design

### Radar chart

- Extend each radar point with an `assessed` flag.
- Keep all five axes and grid lines visible so the chart structure remains
  stable.
- Build the filled data polygon only when at least three axes are assessed.
- With one or two assessed axes, show their real points and connecting strokes
  without inventing values for unassessed axes.
- Unassessed axes remain listed as `待评估` and do not contribute to the
  overall score.

### Mode switcher

- Keep the current hover descriptions on pointer-capable desktop layouts.
- Hide hover descriptions below the desktop breakpoint, where hover state can
  become sticky after a tap.
- Preserve the existing three-button segmented control and mode behavior.

### Session history

- Render the first 30 filtered sessions.
- Add a `加载更多` button that reveals the next 30 rows.
- Reset the visible count when the search query or subject filter changes.
- Keep filtering client-side for this pass; backend pagination is explicitly
  outside this change.

### Mastery trend

- Store a small per-user snapshot containing the assessment fingerprint and
  average score.
- When the fingerprint changes, compare the stored score with the new score,
  then persist both as the latest comparison.
- When the fingerprint is unchanged after refresh, restore the stored trend
  instead of comparing the current value with itself.
- A difference below two percentage points is displayed as flat.

## Error Handling

- Invalid or missing local trend snapshots are ignored and replaced on the
  next valid assessment.
- Radar values are clamped to the `0..1` range before rendering.
- Existing session loading and filtering behavior remains available if the
  history contains fewer than 30 entries.

## Verification

- Add focused tests for radar projection, session batching, and trend snapshot
  transitions using dependency-free TypeScript helpers.
- Run the full API test suite and the production web build.
- Verify desktop and 390px mobile layouts in the in-app browser.
- Confirm that no delete action is executed during UI verification.

## Scope

This change does not modify API endpoints, database schema, Desmos setup, or
the current session deletion lifecycle.
