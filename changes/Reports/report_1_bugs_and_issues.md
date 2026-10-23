# ForensIQ — Bug Report, Issues & Open Endings

> [!IMPORTANT]
> This report is **read-only analysis**. No code has been changed. Each issue includes a severity, location, explanation, and a suggested fix.

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical (breaks functionality) | 4 |
| 🟠 High (incorrect behavior / data loss) | 7 |
| 🟡 Medium (edge cases / robustness) | 8 |
| 🔵 Low (cosmetic / maintenance) | 6 |

---

## 🔴 Critical Issues

### C-1. Typo in Hero — "ForesnIQ" instead of "ForensIQ"

**File:** [Hero.jsx](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/components/Hero.jsx#L19)
**Line:** 19

```js
const SENTENCE_WORDS = ['Welcome', 'To', 'ForesnIQ'];
//                                          ^^^^^^^^ typo
```

**Impact:** The very first thing the user sees on the pitch-deck landing page is a misspelled product name.

**Fix:** Change `'ForesnIQ'` → `'ForensIQ'`.

---

### C-2. Hero Cyan Highlight Condition Targets a Word That Doesn't Exist

**File:** [Hero.jsx](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/components/Hero.jsx#L99)
**Lines:** 99–102

```jsx
${word === 'days.'
  ? 'text-[#00f2ff] drop-shadow-[0_0_25px_rgba(0,242,255,0.35)]'
  : 'text-[#dce4e4]'
}
```

The condition checks for `'days.'`, but `SENTENCE_WORDS` is `['Welcome', 'To', 'ForesnIQ']`. No word will ever match — the cyan glow is never applied to any word.

**Impact:** The hero headline is entirely in the default grey color; the intended design accent is dead code.

**Fix:** Change `word === 'days.'` to `word === 'ForensIQ'` (after fixing the typo in C-1), so the product name glows cyan.

---

### C-3. `InvestigationTimeline.jsx` Is Orphaned / Dead Code

**File:** [InvestigationTimeline.jsx](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/components/dashboard/InvestigationTimeline.jsx)

This entire 126-line component is **never imported** anywhere. The `Dashboard.jsx` imports `Timeline.jsx` instead (which supersedes it, as stated in Timeline.jsx's own header comment: *"Replaces the static InvestigationTimeline component"*).

**Impact:** Dead code bloating the bundle; potential confusion for developers who might edit the wrong file.

**Fix:** Delete `InvestigationTimeline.jsx`, or at minimum add a `// DEPRECATED` header.

---

### C-4. `useMotionValueEvent` Imported But Never Used

**File:** [Hero.jsx](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/components/Hero.jsx#L6)
**Line:** 6

```js
import { ..., useMotionValueEvent } from 'framer-motion';
```

This import is unused. While tree-shaking will remove it in production, it triggers ESLint warnings and can confuse developers.

**Fix:** Remove `useMotionValueEvent` from the import statement.

---

## 🟠 High Severity Issues

### H-1. `_normalize_timestamp` — Incorrect FILETIME-to-Unix Conversion

**File:** [extractor.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/extractor.py#L131-L132)
**Lines:** 131–132

```python
if value > 10000000000000000:
    unix_ts = (value - 116444736000000000) / 10000000
```

Windows FILETIME uses 100-nanosecond intervals, so the divisor should be `10_000_000` (10 million). The code has `10000000` which is correct numerically, **but** the threshold `10000000000000000` is too low — it's `10^16`, while valid FILETIMEs from 2004-era Windows XP are around `127 × 10^15` (`1.27 × 10^17`). The threshold coincidentally works but is fragile.

The real bug: the heuristic path for values `> 1000000000000` assumes **millisecond** epoch — but pyevt can return timestamps as Python `datetime` objects, not raw numbers. If a non-FILETIME large integer (e.g., a nanosecond epoch) hits this path, the conversion silently produces wrong timestamps.

**Impact:** Potentially incorrect timestamps in the timeline for edge-case numeric values.

**Fix:** Add explicit type checking before the numeric heuristic. Consider a dedicated FILETIME detection range `(116444736000000000 < value < 200000000000000000)`.

---

### H-2. `build_macb_features` — "Future Modified" Feature Uses Current Wall-Clock Time

**File:** [feature_engineering.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/feature_engineering.py#L35-L37)
**Lines:** 35–37

```python
now_ts = int(pd.Timestamp.now().timestamp())
df["future_m"] = (df["m_time"] > now_ts).astype(int)
df["zero_size_recent"] = ((df["size"] == 0) & (now_ts - df["m_time"] < 86400)).astype(int)
```

For a **forensic** tool analyzing a Windows XP image (timestamps from ~2004), comparing against `now()` in 2026 means:
- `future_m` will always be 0 (no 2004 timestamp exceeds 2026).
- `zero_size_recent` will always be 0 (no modification within the last 24 hours of a 22-year-old image).

These features are always zero → they contribute nothing to the Isolation Forest model → wasted feature columns.

**Impact:** Two out of six features are always zero, reducing the model's effective dimensionality by 33%.

**Fix:** Derive `now_ts` from the maximum timestamp in the dataset (or accept it as a parameter), not from wall-clock time. For example:
```python
now_ts = int(df["m_time"].max())
```

---

### H-3. `anomaly_detection.py` — Threshold Percentile Doesn't Match IsolationForest Logic

**File:** [anomaly_detection.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/anomaly_detection.py#L56)
**Line:** 56

```python
threshold = np.percentile(scores, CONTAMINATION * 100)
```

`CONTAMINATION` defaults to `0.05`, so this computes the **5th percentile** of the scores. However, `IsolationForest.decision_function` already uses its own internal threshold (offset at 0) to determine anomalies, and `predict()` labels based on that threshold. The chart's drawn threshold line **may not match** the actual label boundary — it's an independent percentile calculation that only coincidentally aligns.

**Impact:** The red threshold line on the chart can be misleading — it may visually disagree with which files were actually flagged.

**Fix:** Use the model's actual threshold: the score at which `predict()` transitions from +1 to -1. This is available as `model.offset_` (added to scores internally). The correct threshold is:
```python
threshold = -model.offset_
```

---

### H-4. `build_log_gap_features` — Output Not Used by Anomaly Detection

**File:** [feature_engineering.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/feature_engineering.py#L49)

The function `build_log_gap_features()` writes `log_gap_features.csv`, but **nothing reads it**:
- `build_feature_matrix()` only reads `macb_features.csv`.
- `anomaly_detection.py` only loads `X_matrix.npy`.
- `timeline.py` doesn't use it either.

**Impact:** The log gap analysis is completely orphaned — it runs, computes features, saves to disk, and is never consumed. This is an incomplete feature pipeline.

**Fix:** Either integrate `log_gap_features.csv` into `build_feature_matrix()` (e.g., by joining on timestamp range or merging as global context features), or remove the function to avoid confusion.

---

### H-5. `extract_evtx` — `.endswith()` on Bytes Object May Fail

**File:** [extractor.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/extractor.py#L315)
**Line:** 315

```python
if not name.endswith(b".evtx"):
```

`name` is `entry.info.name.name`, which is `bytes`. The check against `b".evtx"` is case-sensitive. Windows often stores filenames like `Security.evtx` or `Application.Evtx` — different cases won't match.

Same issue in `extract_prefetch` at line 366:
```python
if not name.endswith(b".pf"):
```

**Impact:** On case-insensitive NTFS images, legitimate `.Evtx` or `.PF` files could be silently skipped.

**Fix:** Use `name.lower().endswith(b".evtx")` and `name.lower().endswith(b".pf")`.

---

### H-6. `run_pipeline.py` Runs Each Step as a Subprocess — Errors Are Silently Incomplete

**File:** [run_pipeline.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/run_pipeline.py#L71-L77)
**Lines:** 71–77

```python
def run_step(name, script):
    result = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
    if result.returncode != 0:
        ...
```

Each step runs as a completely separate process. If a step **prints an error** but returns exit code 0, the pipeline treats it as successful. For example, `feature_engineering.py`'s `main()` doesn't return a non-zero exit code if `build_macb_features()` crashes — it would just raise an unhandled exception, which `subprocess.run()` captures as returncode 1 by coincidence (Python's default behavior on unhandled exceptions), but it's not explicit.

More critically, the step output (`stdout`/`stderr`) is not captured or logged — it goes to the console mixed with the pipeline's own output, making post-mortem analysis difficult.

**Fix:** Add `capture_output=True` and log stdout/stderr, or at minimum add explicit `sys.exit(1)` calls in each module's `main()` function for error paths.

---

### H-7. `timeline.py` — Dashboard Chart Image Path Is Relative and Fragile

**File:** [timeline.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/timeline.py#L488)
**Line:** 488

```python
chart_html = '<img ... src="anomaly_scores.png" ...>' if os.path.exists(chart_path) else ...
```

The `<img>` tag uses a **relative path** `anomaly_scores.png`. This only works if `dashboard.html` is opened from the `reports/` directory. If the HTML is moved or opened from a different working directory, the image breaks.

Similarly, the timeline link in the dashboard (`href="timeline/timeline.html"`) and the dashboard link in the timeline (`href="../dashboard.html"`) assume a rigid directory structure.

**Impact:** Reports break if the output directory structure is altered.

**Fix:** Either embed the image as a base64 data URI, or document the constraint clearly. For portability, base64 embedding is preferable for offline forensic reports.

---

## 🟡 Medium Severity Issues

### M-1. `extract_mft` — Bare `except Exception` Swallows All Errors

**File:** [extractor.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/extractor.py#L88)
**Line:** 88

```python
except Exception:
    continue
```

While the comment says *"Unreadable filesystem entries are common in forensic images"*, this silently swallows **all** exceptions, including programming errors (e.g., `TypeError`, `AttributeError`). A corrupted MFT could silently produce an incomplete dataset without any warning.

**Fix:** Log a count of skipped entries, or at least print a warning with the exception type:
```python
except Exception as exc:
    skipped += 1
    continue
# After loop: print(f"[i] Skipped {skipped} unreadable entries")
```

---

### M-2. `config.py` — Default Image Path Points to a Nonexistent File

**File:** [config.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/config.py#L7)
**Line:** 7

```python
os.path.join(BASE_DIR, "images", "SCHARDT_COMPLETE.dd"),
```

There is no `images/` directory in the project. The pipeline will immediately fail with a "Disk image not found" error.

**Impact:** First-time users hit an error without any guidance on where to place their disk image.

**Fix:** This is partly by design (users must provide their own image), but consider making the default `None` and printing clear instructions when no image is configured.

---

### M-3. `build_macb_features` — No Guard Against Empty MFT

**File:** [feature_engineering.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/feature_engineering.py#L25-L29)
**Lines:** 25–29

If `mft_records.json` is empty or contains no files (all entries are directories), `df[df["type"] == "file"]` returns an empty DataFrame. The function will proceed to save an empty CSV, and `build_feature_matrix()` will then crash on `StandardScaler.fit_transform()` with a zero-row matrix, or produce a zero-row `X_matrix.npy` that causes `IsolationForest.fit()` to raise an error.

**Fix:** Add an early return with a clear error message if the filtered DataFrame is empty.

---

### M-4. `feature_engineering.py` — `build_feature_matrix()` Assumes `macb_features.csv` Exists

**File:** [feature_engineering.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/feature_engineering.py#L98)
**Line:** 98

```python
macb = pd.read_csv(os.path.join(FEAT_DIR, "macb_features.csv"))
```

No `try/except` or existence check. If the previous step failed or was skipped, this will crash with an unhelpful `FileNotFoundError`.

**Fix:** Add `os.path.exists()` check with a descriptive error message.

---

### M-5. `anomaly_detection.py` — No Guard for Empty Feature Matrix

**File:** [anomaly_detection.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/anomaly_detection.py#L17)
**Line:** 17

```python
X = np.load(os.path.join(FEAT_DIR, "X_matrix.npy"))
```

If the feature matrix is empty (0 rows), `IsolationForest.fit(X)` will raise a `ValueError`. No guard exists.

**Fix:** Check `X.shape[0] > 0` and exit gracefully if the matrix is empty.

---

### M-6. `timeline.py` — `ts_to_dt` Treats `0` as a Valid Timestamp

**File:** [timeline.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/timeline.py#L27-L28)
**Lines:** 27–28

```python
def ts_to_dt(unix_ts):
    if not unix_ts:
        return None
```

`not 0` is `True`, so a UNIX timestamp of `0` (1970-01-01) is treated as "no timestamp" and filtered out. While epoch 0 is unusual, it can appear in corrupted MFT entries and might be a valid forensic artifact.

**Fix:** Use `if unix_ts is None:` or explicitly `if unix_ts in (None, "", 0):` depending on the desired behavior.

---

### M-7. `requirements.txt` — `rich` and `tabulate` Are Listed But Never Used

**File:** [requirements.txt](file:///d:/Projects/ForensIQ-main/ForensIQ-main/requirements.txt#L9-L10)
**Lines:** 9–10

```
rich==13.7.1
tabulate==0.9.0
```

Neither `rich` nor `tabulate` is imported in any Python file.

**Impact:** Unnecessary dependencies increase install time and potential version conflicts.

**Fix:** Remove unless they're planned for future features.

---

### M-8. `NetworkGraph.jsx` — Hardcoded Maximum of 4 Anomaly Nodes

**File:** [NetworkGraph.jsx](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/components/dashboard/NetworkGraph.jsx#L46)
**Line:** 46

```js
for (let i = 0; i < Math.min(anomalyCount, 4); i++) {
```

If `anomalyCount` exceeds 4, extra anomaly nodes are silently ignored. The prop `anomalyCount` is passed as 4 from Dashboard.jsx, but the mock data has 5 anomalies.

**Fix:** Dynamically generate positions for any number of anomaly nodes, or document the 4-node limit.

---

## 🔵 Low Severity Issues

### L-1. `SuspiciousFilesTable.jsx` — `.toFixed(2)` Called Without Null Guard

**File:** [SuspiciousFilesTable.jsx](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/components/dashboard/SuspiciousFilesTable.jsx#L139)
**Line:** 139

```jsx
{file.score.toFixed(2)}
```

If `file.score` is `null` or `undefined`, this throws a runtime error. No null guard exists.

**Fix:** Use `(file.score ?? 0).toFixed(2)`.

---

### L-2. `forensiq-ui` — No `favicon.svg` File Exists

**File:** [index.html](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/index.html#L5)
**Line:** 5

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
```

No `favicon.svg` exists in the `public/` directory (which appears empty). Browser console will show a 404 error.

**Fix:** Add a favicon SVG file, or remove the link.

---

### L-3. `forensiq-ui` — Google Fonts Loaded Without Fallback Consideration

**File:** [index.html](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/index.html#L13-L16)

The app loads Inter and JetBrains Mono from Google Fonts CDN. If the CDN is unavailable (e.g., offline forensic environment), the fonts will fail to load silently, falling back to `system-ui` and `Menlo`. This is acceptable but should be noted — forensic tools are often used in air-gapped environments.

**Fix:** Consider self-hosting the fonts or using `@font-face` with local files for offline compatibility.

---

### L-4. `timeline.py` — HTML Not Minified for Large Timelines

**File:** [timeline.py](file:///d:/Projects/ForensIQ-main/ForensIQ-main/timeline.py#L380-L445)

The timeline HTML embeds all event cards directly into the HTML. For large disk images with thousands of flagged anomalies and event log entries, the HTML file could become very large (tens of MB), causing browsers to struggle.

**Fix:** Consider paginating the events, or loading them from a separate JSON file using JavaScript.

---

### L-5. Python Backend + React UI Are Completely Disconnected

The React UI (`forensiq-ui/`) uses **hardcoded mock data** from `mockState.json` and has **zero integration** with the Python backend pipeline. There is no API, no file reading, no data bridge. They are two separate projects sharing a repository.

**Impact:** The UI is purely a visual demo/pitch deck. It does not display real forensic results.

**Fix:** This appears intentional (the UI is a pitch deck), but if real data integration is planned, an API layer or a build step that transforms Python output into the UI's JSON format is needed.

---

### L-6. `Dashboard.jsx` — `formatScanTime` Depends on Browser Locale

**File:** [Dashboard.jsx](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/components/Dashboard.jsx#L105-L117)

```js
function formatScanTime(isoString) {
  const d = new Date(isoString);
  return d.toLocaleString('en-US', { ... });
}
```

Hardcoding `'en-US'` locale is fine, but `timeZoneName: 'short'` will display the **user's local timezone name**, not UTC. A forensic tool should always display UTC to avoid confusion across jurisdictions.

**Fix:** Add `timeZone: 'UTC'` to the options object.

---

## Open Endings / Incomplete Features

| # | Feature | Status | Location |
|---|---------|--------|----------|
| 1 | **Log gap features** | Computed but never consumed by anomaly model | [feature_engineering.py:49](file:///d:/Projects/ForensIQ-main/ForensIQ-main/feature_engineering.py#L49) |
| 2 | **USB history extraction** | Extracts raw SYSTEM hive but never parses USBSTOR keys | [extractor.py:392](file:///d:/Projects/ForensIQ-main/ForensIQ-main/extractor.py#L392) |
| 3 | **Prefetch parsing** | Extracts raw `.pf` files but only records name/size/mtime — no execution count or dependency parsing | [extractor.py:354](file:///d:/Projects/ForensIQ-main/ForensIQ-main/extractor.py#L354) |
| 4 | **Modern EVTX support** | Code exists but Windows XP images won't have `.evtx` files — untestable with stated target | [extractor.py:298](file:///d:/Projects/ForensIQ-main/ForensIQ-main/extractor.py#L298) |
| 5 | **React UI ↔ Python backend** | Completely disconnected; UI uses hardcoded mock data | [mockState.json](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/data/mockState.json) |
| 6 | **`App.jsx` placeholder** | Comment says `"(Future) — Additional pitch modules slot in below"` — nothing follows | [App.jsx:10](file:///d:/Projects/ForensIQ-main/ForensIQ-main/forensiq-ui/src/App.jsx#L10) |
| 7 | **`rich`/`tabulate` dependencies** | Listed in requirements but unused — possibly planned for future CLI output | [requirements.txt:9-10](file:///d:/Projects/ForensIQ-main/ForensIQ-main/requirements.txt#L9) |

---

> [!NOTE]
> This report covers all Python backend modules (`config.py`, `extractor.py`, `feature_engineering.py`, `anomaly_detection.py`, `run_pipeline.py`, `timeline.py`) and all React frontend components (`App.jsx`, `Hero.jsx`, `Dashboard.jsx`, `Navbar.jsx`, `MetricCard.jsx`, `SuspiciousFilesTable.jsx`, `Timeline.jsx`, `NetworkGraph.jsx`, `InvestigationTimeline.jsx`).
