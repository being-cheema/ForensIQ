# Image 4: blind check, written before the image was unpacked

Image: DFIR Madness Case 001 "The Stolen Szechuan Sauce", Windows 10 desktop (DESKTOP-SDN1RPT), `DESKTOP-E01.zip`
(published MD5 71C5C3509331F472ABCDF81EB6EFFF07), https://dfirmadness.com/the-stolen-szechuan-sauce/ .
Answer key: https://dfirmadness.com/answers-to-szechuan-case-001/ .

Frozen before any run on this image:
- features: the 19 final features (`FORENSIQ_FEATURE_SET=final`), unchanged;
- detector: Isolation Forest, 200 trees, subsample 256, seeds 42, 1337, 9999, 7, 2024;
- budgets: 15% and 20%; rule: all targets caught at 20% in every seed (fixed budget, as for Images 1 to 3);
- comparison: best plain rule, as in A3 (R3 location rule, R4 most recent first);
- Wilson 95% intervals over targets.

Targets, from the desktop files the public key names (patterns in `multimodel_eval.py`, `IMG4_TARGETS`):
1. coreupdater.exe, the meterpreter payload installed as a service, with its Prefetch and shortcut traces (pattern `coreupdate`);
2. loot.zip, staged for exfiltration (pattern `loot.zip`);
3. Szechuan Sauce.txt (pattern `szechuan sauce`).

The key names only these desktop files, so there are three targets; a target that has no file in the image is dropped and reported, not replaced.
Nothing in the tool, the features or the rules is changed after the first score on this image. A failed rule is reported as failed.

## Image 5: the domain controller of the same case (added before it was unpacked)
Image: `DC01-E01.zip`, Windows Server 2012 R2 (CITADEL-DC01), same site. Same frozen pipeline, seeds, budgets and rules as above.
Targets, from the files the public key names on the domain controller (`IMG5_TARGETS`): coreupdater.exe (pattern `coreupdate`),
Szechuan Sauce.txt, Secret_Beth.txt, Beth_Secret.txt, PortalGunsPlans.txt and secret.zip. Targets with no file on the disk are dropped and reported.
Prefetch is normally off on servers, so the Prefetch features may fire weakly; this is noted, not patched.
