# PT Course Due-Date Audit

## Data Sources Reviewed
1. `C:\Users\treyt\OneDrive\Desktop\PT School\reference\MASTER_DUE_DATES.txt` (generated Nov 9) – lists per-course totals and identifies 48 Blackboard-derived deadlines.
2. `C:\Users\treyt\OneDrive\Desktop\PT School\reference\COMPLETE_MASTER_DUE_DATES_NOV_10.txt` – narrative schedule that includes the Human Anatomy + PT Exam Skills items missing from the structured summary.
3. Physical folder check: `PT School/courses/` contains all five course directories (Clinical Pathology, Human Anatomy, Legal and Ethical Issues, Lifespan Development, PT Exam Skills) with week-level subfolders, confirming storage alignment.

## Counts & Spot Checks
| Course | Count (MASTER_DUE_DATES) | Sample Entries Verified |
| --- | --- | --- |
| Clinical Pathology | 22 | `9/6 Assignment`, `10/31 Exam 2`, `12/1 Exam 3` |
| Legal & Ethical Issues | 14 | `11/4 Assignment`, `11/8 Final Assignment` (both duplicated for CDT/CST) |
| Lifespan Development | 2 | `9/5 Course orientation` (duplicated timezone) |
| Human Anatomy | 6 (per GAMEPLAN.md:72) | `COMPLETE_MASTER...` documents lectures/labs for Nov 11–13 plus TMJ sessions; Exam 3 placeholder Dec 10 |
| PT Exam Skills | 4 (per GAMEPLAN.md:74) | `COMPLETE_MASTER...` confirms quiz window (11/13–11/16) and weekly labs |

**Total:** 22 + 14 + 2 + 6 + 4 = 48 due dates, matching `GAMEPLAN.md:70-74` and `STATUS.md:140`.

## Findings
- The structured `MASTER_DUE_DATES.txt` is slightly stale—Human Anatomy and PT Exam Skills are labeled "NOT EXTRACTED" even though the narrative file records their schedules. We should regenerate the master list from the latest Blackboard scrape to remove this inconsistency.
- There are duplicate entries for timezone variants (CST/CDT) in Clinical Pathology and Legal & Ethical; when counted as unique due dates the total still matches 48, but HALF B may want to normalize duplicates using UID hashes.
- No corruption detected in `PT School/courses`; each course folder contains week-level materials that align with the due dates listed above, so downstream automation (dashboard + StudyMCP) can rely on this structure.

## Next Actions
1. Re-run the Blackboard agent to refresh `MASTER_DUE_DATES.txt`, ensuring the file itself reflects the 6 Anatomy + 4 Exam Skills items already captured narratively.
2. Store the consolidated JSON (referenced in `MASTER_STUDY_PLAN.md:216`) alongside the text files so automation can query counts without parsing prose.
