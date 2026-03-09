# Literature Review: Convergent Chain-of-Thought Behavior in LLM Proof Verification and Its Correlation with Proof Complexity

## Research Area Overview

This research investigates whether LLM proof verification accuracy under chain-of-thought (CoT) prompting exhibits convergent behavior that correlates with established proof complexity measures. The hypothesis posits that verification accuracy stabilizes after a threshold number of CoT reasoning steps, and this convergence rate is predictable from the structural complexity of the proof being verified. This topic sits at the intersection of three fields: (1) chain-of-thought reasoning in LLMs, (2) proof complexity theory, and (3) test-time compute scaling.

---

## Key Definitions

### Chain-of-Thought (CoT) Reasoning

**Chain of thought** (Wei et al., 2022): A coherent series of intermediate natural language reasoning steps that lead to the final answer. CoT prompting augments few-shot exemplars with intermediate reasoning demonstrations.

**Process supervision** (Lightman et al., 2023): Providing feedback for each individual reasoning step, as opposed to outcome supervision which evaluates only the final answer. Process Reward Models (PRMs) predict correctness probability per step; solution-level score = product of all per-step probabilities.

**Generative verification** (Shi & Jin, 2025): Treating verification as a generative reasoning task where a verifier LLM produces a full CoT reasoning trace walking through a solution step-by-step, culminating in a binary judgment.

### Proof Complexity Measures

**Resolution proof system** (Ben-Sasson & Wigderson, 2001): Proofs where all assertions are clauses (disjunctions of literals). Resolution derives new clauses via: (E ∨ x) and (F ∨ ¬x) → (E ∨ F).

**Proof length (size)**: Number of clauses in a resolution refutation. Can be exponential in formula size.

**Proof width**: Maximum number of literals in any clause appearing in the proof. Always ≤ n (number of variables).

**Proof depth**: Height of the proof DAG. For tree-like proofs, depth equals space complexity.

**Proof space** (Jarvisalo et al., 2012): Maximum number of clauses simultaneously in memory during proof execution. Hierarchy: space ≥ width ≥ log(length).

**Resolution complexity**: The minimum proof length over all valid resolution proofs of a given formula.

### Convergence Concepts

**Test-time compute scaling** (Snell et al., 2024): Allocating additional computation at inference time via search and/or verification. The compute-optimal strategy depends on both problem difficulty and compute budget.

**Information gain** (Ton et al., 2025): Conditional mutual information I(Y; X^M_j | X^M_{j-1}) measuring how much each CoT step contributes toward the correct answer. Drops to zero at the point of reasoning failure.

---

## Key Papers

### Paper 1: Chain-of-Thought Prompting Elicits Reasoning in Large Language Models
- **Authors**: Wei, Wang, Schuurmans, Bosma, et al.
- **Year**: 2022 (arXiv: 2201.11903)
- **Main Results**: CoT is an emergent ability of model scale (≥100B parameters). Provides largest gains on multi-step problems; single-step problems see negligible benefit. PaLM 540B + CoT: GSM8K 56.9% (vs. 17.9% standard). Performance across exemplar orderings shows low variance (±0.4%), suggesting stability/convergence.
- **Proof Techniques**: Ablation studies showing reasoning content (not just extra tokens) drives improvement.
- **Relevance**: Establishes the foundational CoT framework. The finding that CoT benefits scale with problem complexity directly supports investigating correlation with proof complexity measures.

### Paper 2: Let's Verify Step by Step
- **Authors**: Lightman, Kosaraju, Burda, Edwards, et al. (OpenAI)
- **Year**: 2023 (arXiv: 2305.20050)
- **Main Results**: PRMs outperform ORMs at all N in best-of-N evaluation; gap widens with N. Best-of-1860: PRM 78.2% vs. ORM 72.4% vs. majority voting 69.6%. PRM curve continues rising with no saturation up to N=1860; ORM plateaus earlier. Active learning yields 2.6× data efficiency improvement.
- **Relevance**: Demonstrates that step-level verification provides increasingly better discrimination with more candidates—a form of convergent refinement. The widening PRM-ORM gap suggests process supervision captures proof structure information that outcome supervision misses.

### Paper 3: Scaling LLM Test-Time Compute Optimally
- **Authors**: Snell, Lee, Xu, Kumar (UC Berkeley, Google DeepMind)
- **Year**: 2024 (arXiv: 2408.03314)
- **Main Results**: Compute-optimal scaling achieves 4× improvement over best-of-N baselines. Accuracy as a function of test-time compute follows saturation curves that depend on difficulty: easy problems saturate fast, medium problems continue improving, hard problems barely move. The optimal strategy is difficulty-dependent.
- **Proof Techniques**: Formal framework defining compute-optimal scaling strategy as argmax over hyperparameters. Difficulty (pass@1 rate) serves as sufficient statistic.
- **Relevance**: **Core evidence for convergence hypothesis.** Demonstrates verification accuracy convergence that correlates with problem difficulty. The saturation curves provide the template for what we predict: convergence rate correlating with proof complexity.

### Paper 4: Short Proofs Are Narrow—Resolution Made Simple
- **Authors**: Ben-Sasson, Wigderson
- **Year**: 2001
- **Main Results**: Width-size relation for general resolution: w(F ⊢ 0) ≤ w(F) + O(√(n·ln S(F))). Equivalently: S(F) = exp(Ω((w(F⊢0) - w(F))² / n)). Width is characterized by expansion of compatible sensitive functions (Theorem 5.9). High expansion ⟹ large width ⟹ large size.
- **Proof Techniques**: Restriction-based induction; subadditive complexity measures; expansion arguments.
- **Relevance**: **Foundational proof complexity reference.** Provides the formal measures (width, length, depth) whose correlation with CoT convergence we hypothesize. The width-size tradeoff may predict the number of CoT steps needed for verification convergence.

### Paper 5: Relating Proof Complexity Measures and Practical Hardness of SAT
- **Authors**: Jarvisalo, Matsliah, Nordstrom, Zivny
- **Year**: 2012
- **Main Results**: Resolution space complexity correlates most strongly with practical CDCL solver hardness, more so than length or width. Formulas with identical length (O(n)) and width (O(1)) but varying space show orders-of-magnitude differences in solver time tracking space. Hierarchy: space ≥ width ≥ log(length).
- **Relevance**: Establishes that different proof complexity measures predict different aspects of difficulty. Space may be a better predictor of LLM verification difficulty than length or width alone.

### Paper 6: Heimdall: Test-Time Scaling on Generative Verification
- **Authors**: Shi, Jin (ByteDance Seed)
- **Year**: 2025 (arXiv: 2504.10337)
- **Main Results**: Verification accuracy converges: 94.5% single-pass → 97.5% with 64× majority voting (AIME2024). Clear saturation curve with ~2.5% residual error representing systematic model bias. **Problem-solving difficulty does NOT necessarily correlate with verification difficulty**—wide dispersion in the scatter plot.
- **Relevance**: **Key finding for our hypothesis.** Provides direct evidence of convergent verification behavior with saturation. The decorrelation between solving difficulty and verification difficulty suggests verification difficulty may correlate with different structural properties (possibly proof complexity measures).

### Paper 7: Typed Chain-of-Thought: A Curry-Howard Framework for Verifying LLM Reasoning
- **Authors**: Perrier
- **Year**: 2025 (arXiv: 2510.01069)
- **Main Results**: Maps CoT to typed proof terms via Curry-Howard correspondence. Strict-certified runs achieve 91.6% accuracy vs. 42.4% for rejected runs. Identifies a "typed reasoning gradient" with 4 levels from unstructured narrative to complete typed proofs. Minimal Path Size (MPS) provides a graded notion of proof depth.
- **Relevance**: **Directly formalizes CoT as proof.** Provides the theoretical bridge between CoT reasoning and proof complexity. The MPS metric enables measuring proof depth of CoT chains. The 4-level gradient connects proof completeness to verification success.

### Paper 8: Understanding Chain-of-Thought in LLMs through Information Theory
- **Authors**: Ton, Taufiq, Liu
- **Year**: 2025 (arXiv: 2411.11984, ICML 2025)
- **Main Results**: Once a model encounters an unidentifiable sub-task, every subsequent CoT step adds zero information about the correct answer (Theorem 3.3). Information gain provides per-step error detection: positive gain = useful step, zero/negative = divergence. Creates sharp phase transition at the point of failure.
- **Relevance**: Provides information-theoretic characterization of CoT convergence/divergence. The "information plateau" after an unidentifiable step formalizes when convergence fails. The framework for measuring per-step contribution connects to proof step complexity.

### Paper 9: Self-Consistency Improves Chain of Thought Reasoning
- **Authors**: Wang, Wei, Schuurmans, Le, et al.
- **Year**: 2022 (arXiv: 2203.11171)
- **Main Results**: Sampling multiple CoT reasoning paths and marginalizing over them (majority voting on final answers) significantly improves accuracy. Works across arithmetic, commonsense, and symbolic reasoning tasks.
- **Relevance**: Self-consistency is a convergence mechanism—accuracy improves with more samples. The rate of convergence may correlate with the complexity of the underlying reasoning.

---

## Known Results (Prerequisite Theorems)

### Proof Complexity Results

| Result | Statement | Source | Used For |
|--------|-----------|--------|----------|
| Width-Size (tree-like) | S_T(F) ≥ 2^{w(F⊢0) - w(F)} | Ben-Sasson & Wigderson 2001 | Lower bounding proof length from width |
| Width-Size (general) | S(F) ≥ exp(Ω((w(F⊢0) - w(F))²/n)) | Ben-Sasson & Wigderson 2001 | Relating width to exponential size lower bounds |
| Space-Width | Space ≥ Width | Atserias & Dalmau 2008 | Establishing complexity hierarchy |
| Measure hierarchy | space ≥ width ≥ log(length) | Multiple authors | Ordering complexity measures |
| Pebbling-Space | S_T(Peb_G) = 2^{Ω(P(G))} | Ben-Sasson & Wigderson 2001 | Connecting graph structure to proof complexity |

### CoT and Verification Results

| Result | Statement | Source | Used For |
|--------|-----------|--------|----------|
| CoT emergence | CoT effective only at ≥100B parameters | Wei et al. 2022 | Establishing model scale requirements |
| PRM > ORM | Process supervision outperforms outcome supervision, gap grows with N | Lightman et al. 2023 | Justifying step-level verification |
| Compute-optimal scaling | 4× efficiency via difficulty-conditioned strategy | Snell et al. 2024 | Framework for convergence analysis |
| Information plateau | Zero information gain after unidentifiable step | Ton et al. 2025 | Theoretical bound on CoT convergence |
| Verification saturation | ~97.5% ceiling with 64× majority voting | Shi & Jin 2025 | Empirical convergence bound |

---

## Proof Techniques in the Literature

### Technique 1: Restriction-Based Induction
Used in Ben-Sasson & Wigderson (2001) for width-size relations. Set variable to 0/1, reduce to smaller formula, apply induction. Could be adapted to analyze how fixing proof structure parameters affects CoT verification difficulty.

### Technique 2: Expansion Arguments
Width lower bounds via expansion of compatible sensitive functions. High expansion → large width → large size. Potential analog: high "reasoning expansion" → more CoT steps needed → slower verification convergence.

### Technique 3: Difficulty Binning and Compute-Optimal Curves
Used in Snell et al. (2024). Bin problems by pass@1 rate, fit saturation curves per bin, derive compute-optimal strategy. Directly applicable: bin proofs by complexity measures, fit convergence curves, test correlation.

### Technique 4: Information-Theoretic Step Analysis
Used in Ton et al. (2025). Measure conditional mutual information per CoT step. Can be applied to measure information gain per verification step as a function of proof complexity.

### Technique 5: Type-Theoretic Verification
Used in Perrier (2025). Map CoT to typed proof terms, type-check each step. Provides a formal mechanism for measuring proof structure in CoT.

---

## Related Open Problems

1. **Does verification difficulty correlate with proof complexity?** Heimdall (2025) shows solving difficulty ≠ verification difficulty. Our hypothesis: verification difficulty correlates with proof complexity measures instead.
2. **What is the optimal proof complexity measure for predicting CoT convergence?** Length, width, depth, or space? Jarvisalo et al. (2012) suggest space may be most informative.
3. **Is the convergence threshold predictable?** Snell et al. (2024) show difficulty-dependent saturation. Can we predict the saturation point from proof structure?
4. **Can type-theoretic frameworks scale beyond arithmetic?** Perrier (2025) works on GSM8K. Extension to formal mathematical proofs is open.

---

## Gaps and Opportunities

1. **No existing work directly correlates CoT convergence with proof complexity measures.** All convergence results use model-specific difficulty (pass@1 rate) rather than structural proof complexity.
2. **Verification difficulty ≠ solving difficulty** (Heimdall). This gap suggests verification has its own complexity measure—potentially related to proof structure.
3. **Information-theoretic analysis hasn't been connected to proof complexity.** Ton et al.'s information gain framework could be mapped to proof step utility.
4. **Type-theoretic CoT verification is nascent.** Perrier's MPS metric provides proof depth but hasn't been correlated with convergence behavior.

---

## Recommendations for Proof Strategy

### Recommended Approach
1. **Empirical convergence measurement:** Use multiple LLMs to verify proofs of known complexity (resolution proofs, Tseitin formulas, pigeonhole instances). Measure accuracy as a function of CoT steps.
2. **Complexity measure correlation:** Compute proof length, width, depth, and space for test instances. Fit convergence curves and test correlation with each measure.
3. **Difficulty binning:** Adapt Snell et al.'s framework—bin proofs by structural complexity, measure convergence rate per bin.

### Key Lemmas to Establish
1. Formal definition of "verification convergence rate" for a given proof
2. Mapping between proof complexity measures and CoT step requirements
3. Bounds on convergence threshold as a function of proof structure

### Potential Obstacles
- Proof complexity measures are defined for propositional proof systems; natural language CoT operates in a different formalism
- LLM verification may depend on training data distribution rather than structural complexity
- The convergence threshold may be model-dependent, complicating universal statements

### Computational Support
- Use SymPy for generating proofs of controlled complexity
- Use NetworkX for graph-based proof structures (Tseitin formulas, pebbling)
- Statistical analysis with NumPy/SciPy for correlation testing
