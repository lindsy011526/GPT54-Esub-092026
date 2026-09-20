---
name: device-review-pipeline
description: Five-stage regulatory review pipeline for medical devices — FDA regulatory intelligence memos, IFU-derived feature/accessory/software analyses, submission document registers, Traditional Chinese TFDA 查驗登記 review guidance, and pre-report question sets feeding a TFDA-format review report. Use whenever the user works on medical device registration review — TFDA 查驗登記 or 變更登記, FDA 510(k), predicate or 類似品 comparison, IFU analysis, submission document lists, 補件 requirements, review reports — and especially when they supply a device description, an IFU, a submission file list, or a prior review report and want analysis, tables, review guidance, or follow-up questions. Trigger on any single stage, not only the full sequence, and also when the user just pastes an IFU, 送件文件清單, or 審查報告 and asks what to make of it.
---

# Medical Device Review Pipeline

A staged workflow for regulatory affairs work on medical devices, oriented around Taiwan TFDA 查驗登記 with US FDA 510(k) context. Each stage produces a standalone deliverable and feeds the next.

## Why this is staged

Regulatory review is cumulative. The predicate analysis constrains what the IFU analysis looks for; the IFU analysis defines the gap register that the document list either closes or confirms; the document list determines which review points are real deficiencies versus labelling omissions; and only then can a review report assert anything. Running a later stage without the earlier context produces generic output that names no specific deficiency — which is the main failure mode to avoid.

So: **check what earlier-stage material already exists in the conversation before starting any stage.** If the user jumps straight to stage 4, use whatever they've given you and say plainly which earlier inputs would sharpen it, but don't refuse to proceed.

## The five stages

| Stage | User supplies | You produce |
|---|---|---|
| 1 | Device name / description | FDA regulatory intelligence memo, 4000–5000 words, performance & safety requirements table, 20 follow-up questions |
| 2 | IFU (any language) | Major features (performance + safety), accessories table, software features table, 20 follow-up questions |
| 3 | Submission document list | Document register table: title, category, description, comments |
| 4 | (uses stages 1–3) | Traditional Chinese review guidance, 4000–5000 words, required-docs table + 10 key review points |
| 5 | Prior review report as template | 30 questions with committed suggested answers, structured to fill that template |

Stage 6 — writing the actual review report — follows naturally once stage 5 answers are confirmed. Use the user's template verbatim for structure.

## Cross-cutting rules

These matter more than any individual stage format.

**Verify before asserting.** Search the FDA 510(k) database and the open record before claiming a clearance exists. Devices are frequently assumed to be cleared when they are not. If nothing is found, say so plainly and build the analysis on the closest real predicate instead — never invent a 510(k) number, a K-number, or a 510(k) Summary. A fabricated clearance is the single most damaging error this workflow can make.

**Marketing claims are not specifications.** Vendor brochures, distributor pages and product websites routinely carry performance figures (angular ranges, accuracy, detection-rate improvements) that appear nowhere in the IFU or the technical file. When you find such a discrepancy, surface it explicitly as a discrepancy rather than adopting the marketing figure. In regulatory review these gaps are findings, not noise.

**Distinguish evidence gaps from labelling gaps.** A specification missing from an IFU but present in a verification report is a labelling deficiency. The same specification missing from both is an evidence deficiency. These get entirely different 補件 treatment and conflating them wastes the applicant's time.

**Read filenames as data.** Document lists carry real signal: revision letters indicate design churn, signature dates reveal version drift against software releases, declarations filed in place of test records indicate something was unavailable, duplicated or mismatched document numbers indicate control problems, future-dated signatures are data-integrity flags. Mine these systematically.

**Prefer files over chat for the long deliverables.** Stages 1, 2, 4 and 5 produce documents the user will keep, revise and circulate. Write them to `/mnt/user-data/outputs/` as `.md` and present them. Stage 3 may be inline if short. After presenting, give a short spoken summary of the two or three findings that matter most — don't restate the document.

**Language.** Stage 4 is always Traditional Chinese. Stage 5 is Traditional Chinese when the target review report is Chinese. Stages 1–3 follow the user's language, defaulting to English. Bilingual users in this domain expect regulatory terms of art (查驗登記, 補件, 類似品, 仿單) to stay in Chinese even inside English prose.

**Word counts are targets, not decoration.** When the user asks for 4000–5000 words, hit it with substance — more requirement rows, more specific findings, deeper rationale — not padding or restated headings.

## Stage 1 — FDA regulatory intelligence memo

Read `references/stage1-fda-memo.md` for the full section structure and the requirements-table column conventions.

Shape: executive summary that leads with what the search actually found → device description as publicly characterized → classification, product codes, pathway, predicate strategy → applicable FDA guidances and recognized standards → what the closest predicate's testing package reveals → the performance and safety requirements table (title | requirements | comments, 25+ rows) → claim construction → recommended sequence → 20 follow-up questions.

The requirements table is the centerpiece. "Requirements" states the substantive expectation; "Comments" gives reviewer-facing rationale and the practical trap. Rows that just name a standard without saying what will actually be scrutinized are wasted.

## Stage 2 — IFU-derived analysis

Read `references/stage2-ifu-analysis.md` for the extraction checklist and table columns.

Open by naming anything the IFU changes about the stage 1 read — manufacturer jurisdiction, access route, architecture, missing specifications. These corrections are the highest-value part of the output because stage 1 relied on public material and the IFU is controlled.

Then: intended use and scope as written → major performance features by subsystem → major safety features organized by hazard class → accessories table → software features table → gap register → 20 follow-up questions.

For the accessories table, probes and similar variants need per-model technical parameters plus their risk classification and validated reprocessing chemistry. For the software table, every feature needs the constraints and safety notes the IFU attaches to it — a feature list without its warnings is not useful for review.

## Stage 3 — Submission document register

Read `references/stage3-doc-register.md` for category conventions.

One table per submission section, preserving the applicant's own section numbering so the register can be used alongside the physical file. Columns: title | category | description | comments. Close with cross-cutting observations.

The comments column is where the work happens. Flag: documents predating the current software or design revision, revision-level mismatches between linked documents (a requirements spec at Rev H against a traceability matrix at Rev F), declarations substituting for records, numbering inconsistencies, date anomalies, and — most importantly — which stage 2 gaps this list closes and which it confirms.

## Stage 4 — Traditional Chinese review guidance

Read `references/stage4-review-guidance.md` for the full structure and the ten standard review-point headings.

Structure: 產品概述與審查定位 (including the two or three points a reviewer must grasp before starting) → 應檢附文件總表 mapping each required document category to the applicant's actual filed documents with 審查重點 and 初步核對結果 → 十大關鍵審查要點, each with 審查目的 / 核對方法 / 判定基準 / 缺失處理 → 補件事項建議清單 in priority order → 核准後管理建議.

Cite 醫療器材管理法 and 醫療器材許可證核發與登錄及年度申報準則 at the level of document categories rather than specific article numbers, and note that current articles govern. Article numbering changes and a confidently wrong 條次 undermines the whole document.

## Stage 5 — Pre-report question set

Read `references/stage5-questions.md` for the grouping scheme and answer conventions.

Thirty questions grouped to match the target review report's own sections, each with a **committed suggested answer** — a draft the user can accept, edit, or replace, not a prompt for them to do the thinking. Mark the questions most likely to become 補件 items.

Mine the template report hard. A prior review report for a comparable device reveals exactly which deficiency patterns that reviewer issues — per-probe biocompatibility, per-probe acoustic output, resolution specifications, DICOM evidence, AI/CADe technical files, 原廠品質檢驗報告, translation errors. Map each pattern onto the current device and ask whether the same exposure exists. This is far more predictive than reasoning from regulation text alone.

Also flag structural mismatches between the template and the current case — a 變更登記 template applied to a 新案 needs its administrative checklist rebuilt, and a template case with an FDA 510(k) to reference behaves differently from one without.

Close with an appendix drafting the predicted 補件 list, grouped the way the template groups it (說明書記載有誤 / 原廠技術資料不完整 / 臨床前測試資料不完整), so it can be lifted directly into the report.

## Handling partial or messy input

Real inputs are rarely clean. Some common cases:

- **IFU is a scanned PDF in Chinese** — read it directly; don't ask the user to transcribe.
- **Document list is a raw folder dump** — the folder path prefixes usually encode the submission section numbering. Preserve them.
- **User supplies a device name only, no description** — search first, then proceed. Ask only if the search comes back genuinely ambiguous between multiple real devices.
- **Device turns out not to exist in any registry** — say so in the first line of your response, then build on the closest analogue. Don't bury this.
- **User asks for a stage out of order** — proceed with what's available and note in one sentence what would sharpen it.
