# Composition fixture policy

`manifest.json` is the source of truth for acceptance images.

Each case records:

- stable `id` and relative `path`;
- one or more labels from the 15-mode contract;
- `kind`: `positive`, `hard_negative`, `degraded`, or `recommendation`;
- source, author, license, and provenance URL for real images;
- expected abstention and recommendation action when applicable.
- `annotation_source`, `review_status`, and `split`; algorithm output is never ground truth;
- a stable source item ID and SHA-256 so the same image cannot leak across calibration and acceptance splits.

Real images must be redistributable. User camera frames and identifiable private data are forbidden.
Synthetic cases must name the deterministic generator and parameters. Images are normalized to a
maximum edge of 320px unless a performance scenario explicitly requires 720p.

## Annotation and review gate

1. Start from an independently annotated source dataset or a human annotation made without viewing
   CameraQ output. Search keywords, heuristics, and CameraQ may nominate candidates, but may not label them.
2. Apply the definitions in `spec.md` to every candidate. Record all applicable labels because the task is
   multi-label. Record confusing-but-absent modes in `negative_for`; a random unrelated image is not a hard negative.
3. Mark uncertain or disputed images as `pending` or `rejected`. Only `accepted` records count toward metrics.
4. Verify the source license permits repository redistribution and retain the source URL, author/dataset,
   license, source item ID, and file digest. Private camera frames and identifiable private data are forbidden.
5. Keep calibration and acceptance source item IDs disjoint. The manifest audit treats cross-split reuse as leakage.

Run the deterministic gate before calibration:

```bash
uv run python -c "from tests.fixtures.composition.validate_manifest import *; assert_acceptance_ready(audit_manifest('tests/fixtures/composition/manifest.json'))"
```

The gate requires 20 accepted real positives and 20 accepted hard negatives per mode, 25 accepted cases
for each degraded category, 50 recommendation cases total, and at least five cases in each recommendation
action group: translation, rotation, closer, and back.

## Wikimedia Commons candidate curation

The curator downloads only commercially redistributable CC/Public Domain thumbnails, normalizes them to
repository-sized JPEGs, records attribution and SHA-256, and leaves every new case as `pending`:

```bash
uv run python -m tests.fixtures.composition.curate_commons_cases
uv run python -m tests.fixtures.composition.curate_commons_cases --mode diagonal
uv run python -m tests.fixtures.composition.curate_commons_cases --mode frame-within-frame
uv run python -m tests.fixtures.composition.curate_commons_cases --mode tunnel
```

After any HTTP 429, stop and wait. Resume only in bounded low-frequency batches, for example:

```bash
uv run python -m tests.fixtures.composition.curate_commons_cases \
  --mode horizontal --max-new 5 --download-delay 10
```

`--max-new` counts only uncached downloads; completed files are reused on the next run.

Reuse already-downloaded source categories across every matching mode without making network requests:

```bash
uv run python -m tests.fixtures.composition.curate_commons_cases --reproject-existing
```

This only expands source-derived candidate proposals. Any changed case is reset to `pending` and still
requires independent review.

Review the generated contact sheets under `review/` without viewing CameraQ predictions. Source categories
are candidate nominations, not final truth. A reviewer must apply the rubric above and explicitly change
each case to `accepted` or `rejected`; pending candidates never enter calibration or acceptance metrics.
Attribution for retained local candidates is generated in `ATTRIBUTION.md`.
The curator merges repeated `(source, source_item_id)` records into one multi-label case. Run
`--deduplicate-only` after changing source mappings and `--reproject-existing` after changing category
mappings; manifest validation also reports any unreferenced files left under `images/real_candidates/`.

Record a review decision without changing the independent source annotation:

```bash
uv run python -m tests.fixtures.composition.review_candidates \
  set commons-rule-of-thirds-positive-00 accepted \
  --reviewer "reviewer-name" \
  --notes "subject and dominant horizon align with thirds anchors"
```

Allowed decisions are `accepted`, `rejected`, `ambiguous`, and `pending`. Accepted Commons cases must
retain a named independent reviewer and notes or the manifest audit fails. Reviewers must not inspect
CameraQ output before deciding labels.

For batch review, open the positive/negative contact sheets first, export the CSV queue, fill only
`decision`, `reviewer`, and `review_notes`, then import it. Proposed labels in the CSV are read-only and
are deliberately ignored during import:

```bash
uv run python -m tests.fixtures.composition.review_candidates \
  export tests/fixtures/composition/review/review-queue.csv
uv run python -m tests.fixtures.composition.review_candidates \
  import tests/fixtures/composition/review/review-queue.csv
```

Alternatively, generate the fully offline visual review page. It shows only source images and proposal
metadata—never CameraQ predictions—and downloads an import-compatible decisions CSV. Decisions,
notes, and reviewer ID are saved in browser-local storage as you work. Accepted, rejected, and ambiguous
decisions require notes; missing notes are highlighted and block export instead of silently producing an
empty CSV:

```bash
uv run python -m tests.fixtures.composition.generate_review_page
# Open tests/fixtures/composition/review/review-queue.html locally.
uv run python -m tests.fixtures.composition.review_candidates \
  import ~/Downloads/composition-review-decisions.csv
```

## Threshold calibration gate

Threshold calibration uses accepted `positive` and `hard_negative` cases only. Every mode must contain
both classes in both the `calibration` and untouched `acceptance` splits. The command refuses to emit a
proposal when a class/split is missing; abstained positives remain false negatives in recall:

```bash
uv run python -m tests.fixtures.composition.assign_calibration_splits
uv run python -m tests.fixtures.composition.calibrate_thresholds
```

The split command deterministically targets 40% of every accepted mode/class stratum for calibration,
keeps each source item in exactly one split, and leaves the remainder untouched for acceptance.
The output proposes per-mode enter/exit thresholds and separately reports calibration and acceptance
precision/recall. It also embeds the exact `weight_config_version` and per-mode evidence-weight snapshot
used to score the images. It never edits `src/core/composition/thresholds.py` automatically.
