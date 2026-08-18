# Consensus Scoring — Tasks

#[[file:.kiro/specs/consensus-scoring/design.md]]

---

## Task 1: Property-based tests (write first)
- [ ] Create `tests/test_consensus.py`:
      - **Determinism**: dock pyrimethamine 3× on pf-dhfr with fixed params,
        assert all consensus_scores are identical.
      - **Active outranks inert**: pyrimethamine consensus < glucose consensus.
- [ ] Mark both `@pytest.mark.slow` and `@pytest.mark.property`.

Traces: REQ-CS-4, REQ-CS-5

---

## Task 2: Vinardo rescoring module
- [ ] Create `valkyrie/rescoring.py`:
      ```python
      def rescore_vinardo(
          ligand_pdbqt: str,
          receptor_pdbqt_path: Path,
          box: DockingBox,
      ) -> float:
      ```
      - Load the docked pose into Vina with `sf_name='vinardo'`.
      - Call `v.score()` to get the Vinardo energy.
      - Return the score (kcal/mol).
- [ ] Write unit test: rescore pyrimethamine pose, assert returns negative float.

Traces: REQ-CS-1

---

## Task 3: Consensus scoring module
- [ ] Create `valkyrie/consensus.py`:
      ```python
      @dataclass
      class ConsensusResult:
          vina_score: float
          vinardo_score: float
          consensus_score: float

      def compute_consensus(
          vina_score: float,
          vinardo_score: float,
          ref_vina: float,
          ref_vinardo: float,
          w1: float = 0.6,
          w2: float = 0.4,
      ) -> ConsensusResult:
      ```
      - Normalize each score relative to the reference drug.
      - Combine with weights.
      - Lower consensus = better binding.
- [ ] Write unit test: known inputs produce expected consensus value.

Traces: REQ-CS-2

---

## Task 4: Extend DockingResult and pipeline
- [ ] Modify `valkyrie/docking.py`: add `vinardo_score` field to `DockingResult`.
- [ ] Modify `valkyrie/pipeline.py`:
      - After docking, call `rescore_vinardo()` on the best pose.
      - Compute consensus using reference drug scores (cached).
      - Add `consensus_score` to `PipelineResult`.
- [ ] Modify `valkyrie/comparator.py`: include consensus in comparison table.

Traces: REQ-CS-1, REQ-CS-2

---

## Task 5: Enrichment benchmarking
- [ ] Create `data/benchmark_pf_dhfr.json`:
      ```json
      {
        "actives": ["pyrimethamine", "cycloguanil", "trimethoprim"],
        "inactives": ["glucose", "ethanol", "caffeine", "aspirin", "ibuprofen"]
      }
      ```
- [ ] Create `valkyrie/benchmarks.py`:
      - `run_benchmark(target_id) -> BenchmarkResult`
      - Dock all actives + inactives, compute AUC-ROC for Vina-only vs consensus.
      - Report EF@10%.
      - Store result in SQLite for `/benchmarks`.
- [ ] Write test: mock docking results, verify AUC calculation is correct.

Traces: REQ-CS-3

---

## Task 6: API endpoint
- [ ] Add `GET /api/benchmarks/{target_id}` to `valkyrie/api.py`:
      - Returns latest benchmark results (AUC, EF, honest comparison).
      - Includes disclaimer: "In-silico benchmark — not a clinical validation."
- [ ] Update `POST /api/dock` response to include `vinardo_score` and
      `consensus_score` fields.
- [ ] Update frontend comparison table to show both scores.

Traces: REQ-CS-2, REQ-CS-3

---

## Task 7: Integration validation
- [ ] Run full test suite (slow + fast), confirm no regressions.
- [ ] Verify consensus determinism test passes.
- [ ] Verify active-outranks-inert test passes.
- [ ] Commit with descriptive message.

---

## Dependency Order
```
Task 1 (tests first)
Task 2 (rescoring) ← needs Vina installed
Task 3 (consensus) ← pure computation
Task 4 (pipeline integration) ← needs 2 + 3
Task 5 (benchmarks) ← needs pipeline working
Task 6 (API) ← needs 4 + 5
Task 7 (validation)
```
