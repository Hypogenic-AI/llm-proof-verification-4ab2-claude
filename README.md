# Convergent Chain-of-Thought Behavior in LLM Proof Verification and Its Correlation with Proof Complexity

## Overview

This project investigates whether classical proof complexity measures (length, width, depth, space) predict how quickly LLM chain-of-thought (CoT) verification converges to a stable answer. We build a computational framework generating 129 synthetic proof instances across four formula families and model CoT verification as a stochastic saturation process calibrated to published empirical data.

## Key Results

- **Proof complexity strongly predicts convergence rate**: Composite complexity measure achieves Spearman ρ = −0.99 (p < 10⁻¹¹³) with convergence rate; R² = 0.93 in multiple regression
- **Proof length governs accuracy ceiling**: Longer proofs yield lower asymptotic accuracy (ρ = −0.77, p < 10⁻²⁵), consistent with error accumulation
- **Phase transition detected**: Verification difficulty steepens 29% beyond critical complexity C* ≈ 12.95 (F-test p = 0.008)
- **Self-consistency cost scales quadratically**: Chains needed for target accuracy scale as O(1/(p − 0.5)²), where p depends on proof complexity

## Reproduction

```bash
source .venv/bin/activate
python -m src.analysis              # Full analysis with visualizations
python -m src.theoretical_analysis  # Formal theorem verification
```

## File Structure

| Path | Description |
|------|-------------|
| `REPORT.md` | Full research report with all results |
| `src/proof_generator.py` | Proof instance generation (Tseitin, PHP, Pebbling, Random k-CNF) |
| `src/verification_model.py` | Stochastic CoT verification model |
| `src/analysis.py` | Correlation analysis and visualization |
| `src/theoretical_analysis.py` | Formal theorem verification |
| `results/` | JSON results files |
| `figures/` | Generated plots |
| `planning.md` | Research plan |
| `literature_review.md` | Literature review |

## Dependencies

Python 3.12+, NumPy, SciPy, NetworkX, Matplotlib, SymPy
