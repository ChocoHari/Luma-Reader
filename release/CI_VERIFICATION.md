# Hosted Windows verification

18 October 2026: GitHub Actions run https://github.com/ChocoHari/Luma-Reader/actions/runs/39113742007 completed successfully for commit 23c1aadf972cbd44cad78ab38d140318b66e4ab0 on the release-preparation branch.

The windows-2025 job installed the locked dependencies into a fresh virtual environment, fetched only the reviewed Cori build voice, passed 62 functional tests, built the standalone executable with its exact source snapshot, passed the standalone diagnostic and verified the candidate portable archive. No binary artifact upload or release publishing step is configured.

The first attempted workflow failed GitHub validation because runner.temp was used in a job-level environment expression. The corrected workflow uses github.workspace for the private CI data directory and ignores that directory in Git. The successful run is the first hosted verification, not a claim that the initial invalid workflow passed.

This verifies the source and build workflow on another Windows environment. GitHub's runner has development runtimes installed; this is not a clean end-user Windows installation test. It does not verify physical speaker audibility, native frame behavior across monitors/scaling, installer wizard appearance or pending dependency distribution obligations. Later source changes require their own successful run.

The stricter model-policy commit 0842c0e2950252bbb2fc90e765a5d44f969e03ae also passed its complete hosted Windows run: https://github.com/ChocoHari/Luma-Reader/actions/runs/39114077277 . Its successful build enforced exactly the reviewed voice and three OCR model paths, with optional Piper package ONNX weights excluded. This supersedes the earlier pending status for that commit.
