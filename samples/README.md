# Sample Outputs

These samples let you inspect what the generator creates without running the app.

## Start Here

- `transcripts_only/` has only the support-call text files.
- `review_pack/` is the best first look for most use cases. It has transcripts plus safe metadata.
- `eval_pack/` adds hidden truth, expected timeline, and leakage reports.
- `process_fixture/` shows the richer support-process fixture export.

## What To Open

For the simplest review:

1. Open one file in `review_pack/transcripts/`.
2. Open the matching file in `review_pack/metadata/`.
3. Compare that with `eval_pack/ground_truth/` if you want to see the hidden answer key.

## Bundle Meanings

- `transcripts_only`: just the call transcripts.
- `review_pack`: transcripts + safe metadata for demos, browsing, review, search, and summarization.
- `eval_pack`: review pack + evaluator-only files.
- `process_fixture`: context events, expected support state, next checks, handoff fields, and outcome fields.

All sample files are synthetic.
