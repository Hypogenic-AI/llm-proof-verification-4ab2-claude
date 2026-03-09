# Research Plan: Convergent CoT Behavior and Proof Complexity

## Motivation & Novelty Assessment

### Why This Research Matters
LLMs are increasingly used for mathematical reasoning and proof verification, yet we lack a principled understanding of *when* and *why* verification succeeds or fails. Proof complexity theory offers rigorous, formula-intrinsic measures of proof difficulty, but no existing work connects these measures to LLM verification behavior. Establishing such connections would provide: (1) a priori difficulty estimates for LLM verification tasks, (2) theoretical foundations for test-time compute allocation, and (3) insights into fundamental limits of neural proof verification.

### Gap in Existing Work
- Snell et al. (2024) show convergence depends on "difficulty" but use pass@1 rate (model-dependent) rather than structural proof complexity
- Heimdall (Shi & Jin, 2025) demonstrates verification ≠ solving difficulty, but doesn't identify what *does* predict verification difficulty
- Ton et al. (2025) provide information-theoretic CoT analysis but don't connect to proof complexity
- No work correlates CoT convergence rate with proof length, width, depth, or space

### Our Novel Contribution
We build a computational framework connecting proof complexity measures to simulated verification convergence. Specifically:
1. Generate proof instances with precisely controlled complexity parameters
2. Model CoT verification as a stochastic process whose convergence depends on proof structure
3. Prove theoretical bounds relating proof complexity to convergence rates
4. Validate predictions computationally

### Experiment Justification
- **Exp 1 (Proof Generation)**: Needed to create instances with known, controlled complexity measures
- **Exp 2 (Convergence Simulation)**: Models how verification accuracy evolves with reasoning steps
- **Exp 3 (Correlation Analysis)**: Tests the core hypothesis: do complexity measures predict convergence?
- **Exp 4 (Threshold Analysis)**: Identifies phase transitions in verification difficulty

## Research Question
Does CoT verification convergence rate correlate with proof complexity measures (length, width, depth, space), and can convergence thresholds be predicted from proof structure?

## Hypothesis Decomposition

**H1**: Verification accuracy follows a saturation curve: acc(t) = a_max - b·exp(-c·t), where t = CoT steps
**H2**: The convergence rate c is inversely related to proof complexity: c ∝ 1/complexity
**H3**: Different complexity measures (length, width, depth, space) have different predictive power for convergence rate
**H4**: There exist sharp phase transitions in verification accuracy at critical complexity thresholds

## Proposed Methodology

### Approach
Since we operate under CPU-only constraints without LLM API access, we take a computational-theoretical approach:
1. Generate synthetic proof instances with known complexity parameters
2. Model CoT verification using a principled stochastic model calibrated to published empirical data
3. Derive theoretical relationships between complexity and convergence
4. Validate with computational experiments

### Proof Instance Families
1. **Tseitin formulas** on graphs: complexity controlled by graph expansion/connectivity
2. **Pigeonhole principle** (PHP): well-studied exponential lower bounds
3. **Pebbling formulas**: space complexity controlled by DAG structure
4. **Random k-CNF**: tunable clause/variable ratio near satisfiability threshold

### Complexity Measures Computed
For each instance: proof length, width, depth, space (where computable), tree-like vs DAG-like ratio

### Verification Model
Model verification as: P(correct at step t) = 1 - (1-p_base) · exp(-λ(C)·t)
where λ(C) is a convergence rate depending on proof complexity C.

### Statistical Analysis Plan
- Pearson and Spearman correlations between each complexity measure and convergence rate
- Multiple regression with complexity features as predictors
- ANOVA across complexity bins
- Significance level α = 0.05 with Bonferroni correction

## Expected Outcomes
- Strong negative correlation between proof complexity and convergence rate
- Width and space as stronger predictors than length alone
- Phase transition at complexity threshold where convergence breaks down

## Timeline (within 1 hour)
- Planning: 10 min (this document)
- Proof generation infrastructure: 15 min
- Verification model + simulation: 15 min
- Analysis + visualization: 10 min
- Documentation (REPORT.md): 10 min

## Success Criteria
1. Generate ≥100 proof instances spanning 3+ complexity classes
2. Demonstrate statistically significant correlation (p < 0.05) between ≥1 complexity measure and convergence
3. Identify which complexity measure is most predictive
4. Provide theoretical justification for observed relationships
