# Resources Catalog

## Summary
Resources gathered for investigating convergent chain-of-thought behavior in LLM proof verification and its correlation with proof complexity measures. The research sits at the intersection of CoT reasoning, proof complexity theory, and test-time compute scaling.

## Papers
Total papers downloaded: 19

| # | Title | Authors | Year | File | Key Results |
|---|-------|---------|------|------|-------------|
| 1 | Chain-of-Thought Prompting | Wei et al. | 2022 | papers/2201.11903_chain_of_thought.pdf | CoT emergent at ≥100B params; bigger gains on harder problems |
| 2 | Let's Verify Step by Step | Lightman et al. | 2023 | papers/2305.20050_lets_verify_step_by_step.pdf | PRM > ORM; gap widens with N; no saturation up to N=1860 |
| 3 | Self-Consistency | Wang et al. | 2022 | papers/2203.11171_self_consistency.pdf | Majority voting over CoT paths improves accuracy |
| 4 | Tree of Thoughts | Yao et al. | 2023 | papers/2305.10601_tree_of_thoughts.pdf | Tree search over reasoning paths |
| 5 | Zero-shot CoT | Kojima et al. | 2022 | papers/2205.11916_zero_shot_cot.pdf | "Let's think step by step" as zero-shot trigger |
| 6 | Scaling Test-Time Compute | Snell et al. | 2024 | papers/2408.03314_scaling_test_time_compute.pdf | Difficulty-dependent saturation; 4× compute efficiency |
| 7 | Heimdall | Shi & Jin | 2025 | papers/heimdall_test_time_scaling.pdf | 94.5%→97.5% convergence; verification ≠ solving difficulty |
| 8 | Typed CoT (Curry-Howard) | Perrier | 2025 | papers/2510.01069_typed_cot_curry_howard.pdf | CoT as typed proof terms; 91.6% precision on certified runs |
| 9 | Verifying CoT Computational Graph | — | 2025 | papers/2510.09312_verifying_cot_computational_graph.pdf | Graph-based CoT verification |
| 10 | CoT Information Theory | Ton et al. | 2025 | papers/2411.11984_cot_information_theory.pdf | Info gain drops to zero at failure; phase transition |
| 11 | LLM Math Reasoning Survey | Ahn et al. | 2024 | papers/2402.00157_llm_math_reasoning.pdf | Comprehensive survey |
| 12 | Safe (Step-aware Verification) | — | 2025 | papers/2501.03055_safe.pdf | Retrospective formal verification |
| 13 | URSA | — | 2025 | papers/2501.04686_ursa.pdf | Multimodal CoT verification |
| 14 | HERMES | — | 2025 | papers/2502.17532_hermes.pdf | Efficient verifiable reasoning |
| 15 | Lean-STaR | — | 2024 | papers/2407.10040_lean_star.pdf | Interleaving thinking and proving |
| 16 | InternLM2.5-StepProver | — | 2024 | papers/2410.15700_internlm_stepprover.pdf | Step-level theorem proving |
| 17 | Short Proofs Are Narrow | Ben-Sasson & Wigderson | 2001 | papers/ben_sasson_wigderson_2001_short_proofs_narrow.pdf | w(F⊢0) ≤ w(F) + O(√(n·ln S)); width-size relations |
| 18 | Proof Complexity & SAT Hardness | Jarvisalo et al. | 2012 | papers/ansotegui_2012_proof_complexity_sat.pdf | Space > width > log(length) for practical hardness |
| 19 | Proof Complexity Survey | Beame & Pitassi | 1998 | papers/beame_pitassi_proof_complexity_survey.pdf | Foundational survey |

See papers/README.md for detailed descriptions.

## Prior Results Catalog

| Result | Source | Statement Summary | Used For |
|--------|--------|-------------------|----------|
| Width-Size (tree-like) | Ben-Sasson & Wigderson 2001 | S_T(F) ≥ 2^{w(F⊢0) - w(F)} | Lower bounding tree-like proof length |
| Width-Size (general) | Ben-Sasson & Wigderson 2001 | S(F) ≥ exp(Ω((w-w₀)²/n)) | Relating width to exponential size bounds |
| Width characterization | Ben-Sasson & Wigderson 2001 | w(F⊢0) ≥ expansion of compatible sensitive functions | Width lower bounds via expansion |
| Space hierarchy | Atserias & Dalmau 2008 | space ≥ width ≥ log(length) | Ordering complexity measures |
| Space predicts hardness | Jarvisalo et al. 2012 | Space correlates with CDCL solver time | Most informative complexity measure |
| CoT emergence | Wei et al. 2022 | Effective only at ≥100B parameters | Model scale requirements |
| PRM scaling | Lightman et al. 2023 | PRM accuracy grows with N; gap widens vs ORM | Step-level verification effectiveness |
| Compute-optimal | Snell et al. 2024 | 4× efficiency; difficulty-dependent saturation | Convergence framework |
| Verification convergence | Shi & Jin 2025 | 94.5%→97.5% with 64× voting; ~2.5% residual | Empirical convergence ceiling |
| Information plateau | Ton et al. 2025 | Zero info gain after unidentifiable step | Theoretical convergence limit |
| Typed CoT | Perrier 2025 | 91.6% precision via type-checking; MPS as depth | Proof structure in CoT |

## Computational Tools

| Tool | Purpose | Location | Notes |
|------|---------|----------|-------|
| SymPy 1.14.0 | Symbolic computation | pip package | Generate proofs, algebraic manipulation |
| NumPy | Numerical computation | pip package | Statistical analysis of convergence data |
| SciPy | Statistical testing | pip package | Correlation tests, curve fitting |
| NetworkX | Graph operations | pip package | Tseitin formula graphs, pebbling DAGs |
| Matplotlib | Visualization | pip package | Convergence curves, correlation plots |

## Resource Gathering Notes

### Search Strategy
1. Primary search via paper-finder service with diligent mode on three query sets:
   - "chain-of-thought reasoning LLM proof verification mathematical"
   - "proof complexity measures resolution complexity depth length"
   - "LLM mathematical reasoning convergence scaling behavior"
2. Additional targeted searches for test-time compute and process reward models
3. Web search for specific papers (e.g., correct arXiv ID for Typed CoT)
4. Direct arXiv downloads for all identified papers

### Selection Criteria
- Papers directly studying CoT convergence behavior (Snell 2024, Heimdall 2025)
- Foundational proof complexity theory (Ben-Sasson & Wigderson 2001, Jarvisalo 2012)
- Formal frameworks connecting CoT to proofs (Perrier 2025, Ton 2025)
- Step-level verification methods (Lightman 2023)
- LLM mathematical reasoning capabilities (surveys and key systems)

### Challenges Encountered
- Two arXiv ID mismatches: 2503.09114 was not Typed CoT (corrected to 2510.01069), 2502.17422 was not Heimdall (corrected to 2504.10337)
- Some proof complexity papers only available behind paywalls; used arXiv/preprint versions where available

## Recommendations for Proof Construction

### 1. Proof Strategy
The most promising approach combines empirical measurement with theoretical analysis:
- **Generate proofs of controlled complexity** using Tseitin formulas (varying graph expansion) and pebbling formulas (varying space complexity) to create instances with known proof complexity measures
- **Measure CoT verification accuracy** across multiple LLMs as a function of reasoning steps
- **Fit convergence curves** per complexity bin and test correlation with each complexity measure (length, width, depth, space)

### 2. Key Prerequisites
- Ben-Sasson & Wigderson's width-size relation (for theoretical grounding)
- Snell et al.'s compute-optimal framework (for experimental methodology)
- Ton et al.'s information gain framework (for per-step convergence measurement)
- Perrier's MPS metric (for measuring proof depth in CoT)

### 3. Computational Tools
- SymPy + NetworkX for generating proof instances of controlled complexity
- Standard statistical tools (SciPy) for correlation analysis
- LLM API access for verification experiments

### 4. Potential Difficulties
- Proof complexity measures are defined for propositional systems; bridging to natural language CoT requires careful formalization
- LLM verification may depend on training distribution rather than structural complexity
- The convergence threshold may be model-dependent, requiring normalization
- Heimdall's finding that verification ≠ solving difficulty suggests the relationship may be more nuanced than direct correlation
