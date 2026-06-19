# Realtime Support Export

The realtime-support export is ready for staging, importer smoke tests, validator checks, and prototype report review.

Generated fixtures are not ready to copy directly into `/Users/aditya/Documents/Projects/real-time_support_Updated/fixtures/` as source-of-truth eval fixtures. In the latest cross-repo check, promoted generated fixtures still left `test_experiment.py` short (`502/504` deterministic, `462/504` process mock), so promotion should wait for expected-state calibration or a generated-fixture evaluation mode.

Generate and export reviewed cases from this repo, then import the envelope into the realtime repo:

```bash
cd /Users/aditya/Documents/Projects/real-time_support_Updated
python3 prototype/import_generated.py /Users/aditya/Documents/Projects/support-call-generator/exports/realtime_support_envelope.json
```

After import, review the staged fixtures and rendered report quality before promoting anything into root fixtures.
