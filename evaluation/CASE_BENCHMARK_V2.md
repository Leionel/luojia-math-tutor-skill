# Teaching Case matching benchmark v2

`case_matching_benchmark_v2.json` is a developer-authored frozen set of **228 unique queries**, separate from the original 20-item benchmark. Gold rationales were not generated from matcher predictions. They identify the query's actual target, mathematical predicate, and nearest excluded Case. No teacher has reviewed these annotations yet; a teacher should check condition contrasts, multi-intent routes, and the in-course `NEW_CASE` judgments before using this as an acceptance gate.

Coverage includes all 15 existing Case families, 13 inert Python code fragments, 15 explicit `task_mode` contexts, 11 out-of-course OOD requests, and 7 in-course requests requiring a Case absent from the frozen ontology. The remaining splits cover near-neighbor conditions, insufficient evidence, mixed intent, uncertainty, and two unrouteable queries. Code fragments are passed only as strings to the matcher; the evaluator never executes query content. Historical dialogue is not fabricated or loaded.

There are 41 Latin-script-only queries, 84 mixed-script queries, and 103 CJK-script-only queries. In the Latin-only script bucket, Case Recall@1 was **1/41 (2.4%)** and strict decision accuracy **1/39 (2.6%)**; the latter excludes its two multi-gold items. This is a rough script proxy, not a clean English test set: it mixes root-finding questions with OOD/new-Case samples and does not isolate language from math notation. Script strata are included for inspection; no claim of English tutoring quality follows from these numbers.

## Protocol and metrics

Every routable single-target item uses a singleton Case gold. Ordinary same-task queries expect `SAME_CASE`; near-neighbor coverage does not itself imply a variant. Under the research specification §4.5, unchanged canonical premises and goals remain `SAME_CASE`; changed conditions, parameters, or representations may use `VARIANT_OF_CASE`. Six mixed-intent items retain explicit acceptable Case and decision sets instead of inventing one primary intent. Two requests with no algorithm or goal are `unroutable`, gold Case `None`, decision `UNCERTAIN`, and excluded from Case Recall@1. The parent review corrected V2-167 and V2-169 against that specification, without consulting predictions to choose their labels.

`singleton_decision_accuracy` is strict decision accuracy over items with exactly one expected decision; the denominator excludes multi-gold items and is reported. `acceptable_set_compatibility` gives credit for any explicitly accepted decision over the full set; it is a looser compatibility measure, not strict accuracy. OOD detection requires both the expected no-Case result and an accepted decision. `new_case_detection` separately scores requests inside the course topic but outside the current Case ontology. These two sets must not be combined.

The evaluator validates required gold fields, rejects empty sets and unknown Case IDs before matching, passes context to `match`, preserves matcher exceptions in denominators, and records every failed sample. Output includes benchmark, course-pack, and matcher-source hashes; denominators; per-split, per-family, and script-based results; and all failures. The runner loads the static pack directly into an in-memory repository. It does not read `.env`, open a persistent store, call a network service, install dependencies, or execute benchmark queries. `--strict` returns nonzero on capability failures; default mode reports them without converting a low score into an evaluator error.

## Reproduce

From the repository root:

```powershell
python evaluation/build_case_v2.py
python evaluation/evaluate_case_benchmark.py --benchmark evaluation/case_matching_benchmark.json --output results/case_benchmark_legacy.json
python evaluation/evaluate_case_benchmark.py --benchmark evaluation/case_matching_benchmark_v2.json --output results/case_benchmark_v2.json
cd apps/api
python -m pytest tests/test_case_benchmark_evaluator.py -q
```

## Recorded run (2026-09-30)

The legacy 20-item set retains its normal result: Case Recall@1 **16/16**, acceptable-set decision compatibility **20/20**, OOD detection **4/4**. Its original decision gold labels are all sets with multiple accepted outcomes, so it has no strict singleton-decision denominator (**0**, all 20 excluded).

For v2, Case Recall@1 was **11/208 (5.3%)**; the two unroutable requests are separately counted and excluded. Strict singleton-decision accuracy was **34/222 (15.3%)**, with six multi-gold decisions excluded. Acceptable-set compatibility was **34/228 (14.9%)**. OOD detection was **10/11 (90.9%)** and in-course new-Case detection **7/7**. There were 204 rows with at least one mismatch, 198 Case mismatches, and 194 decision compatibility mismatches; these counts overlap. There were no matcher exceptions. Scores describe this deterministic matcher against this unreviewed benchmark; they do not establish overall mathematical or tutoring quality.

The weakest current Case families include bisection error bounds, bisection conditions, Newton code update/stopping, residual-versus-error, and Newton initial-value diagnosis, each with zero Case hits in this run. For example, V2-001 is understandable Chinese, but its token overlap with the three bisection-condition variants is only about 0.26–0.29; the matcher returned `NEW_CASE` with no candidates. This is evidence of lexical paraphrase recall limits in this deterministic matcher, not an LLM or mathematical-reasoning evaluation. One OOD QR eigenvalue query matched bisection error bounds, showing a boundary false positive.

Hashes for this run: benchmark `0c263dfc9c8646bcd43f0a77987439f8e97776e45d5efa94edf3e0903ab9e6a0`; course pack `7cc6d187788a27865e0ac46863340bfcc6cfa11787002b0dda7f5029bf05800e`; matcher source `22eec541d33fb4381106a780fe79f82c235cf96929a1a5c31cda63b7b490abf3`.

This work leaves the 244-item retrieval evaluation unchanged. `scripts/eval_retrieval.py`'s graph-layer pending independently weighted-IDF dry run is distinct from the production `EvidenceBuilder`; chunk/unit Recall and hierarchy@1 are not interchangeable metrics.
