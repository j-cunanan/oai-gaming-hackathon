# Existing color-candidate tests and build identity

This audit copies the eight JUnit XML files from the already completed candidate test execution for [md-12623-terra-replay-02](../md-12623-terra-replay-02-final/README.md). It does **not** execute a new test suite, replay or AI request. The files record **276 tests, zero failures, zero errors and zero skips**, run with network enabled at approximately 21:28–21:29 UTC on September 14.

`result.json` binds the target commit, candidate patch, stored test log, exact audit driver, XML timestamps and file hashes. It also records distinct SHA-256 hashes for the retained baseline and candidate JARs and for their compiled ColorPicker classes. These identify the builds; the separate replay evidence establishes that the candidate still has the bug in 5/5 fresh runs. Passing existing tests did not make this candidate a successful fix.

The exact `audit_driver.py` reads existing local outputs. Run it only against those original, unchanged outputs and an absent destination directory. The original offline baseline test failure is retained in the case and is not counted as a successful baseline suite here.
