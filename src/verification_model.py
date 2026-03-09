"""
Stochastic model for CoT verification convergence.

Models LLM proof verification as a stochastic process where:
- Each CoT step provides partial information about proof validity
- Convergence rate depends on proof structural complexity
- The model is calibrated to match published empirical data:
  * Heimdall: 94.5% -> 97.5% with 64x majority voting
  * Snell et al.: difficulty-dependent saturation curves
  * Lightman et al.: PRM accuracy scaling with N

The model captures the key insight: verification difficulty is determined
by proof structure (complexity measures), not solving difficulty.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from src.proof_generator import ProofInstance, compute_normalized_complexity


@dataclass
class ConvergenceResult:
    """Results of convergence simulation for one proof instance."""
    instance_name: str
    family: str
    # Accuracy at each CoT step (1..max_steps)
    accuracy_curve: np.ndarray
    # Step at which accuracy stabilizes (within epsilon of final value)
    convergence_step: int
    # Final (asymptotic) accuracy
    final_accuracy: float
    # Convergence rate (fitted exponential decay parameter)
    convergence_rate: float
    # Complexity features
    complexity_features: Dict[str, float]
    # Model parameters
    base_accuracy: float
    noise_std: float


def verification_accuracy_model(
    instance: ProofInstance,
    max_steps: int = 20,
    n_trials: int = 100,
    model_params: Dict = None,
    seed: int = 42,
) -> ConvergenceResult:
    """
    Simulate CoT verification accuracy as a function of reasoning steps.

    Model: At each step t, the verifier has probability p(t) of being correct,
    where p(t) follows a saturation curve:

        p(t) = p_max - (p_max - p_0) * exp(-lambda * t)

    Key assumptions calibrated from literature:
    1. lambda (convergence rate) is inversely proportional to a weighted
       combination of proof complexity measures
    2. p_max (asymptotic accuracy) decreases with complexity
    3. p_0 (initial accuracy) is near chance (0.5) for hard proofs

    Self-consistency (majority voting over multiple chains):
    For N independent chains, majority vote accuracy at step t is:
        P_maj(t, N) = sum_{k>N/2} C(N,k) * p(t)^k * (1-p(t))^(N-k)

    Args:
        instance: Proof instance with known complexity
        max_steps: Maximum number of CoT steps
        n_trials: Number of independent verification attempts per step
        model_params: Override default model parameters
        seed: Random seed
    """
    rng = np.random.RandomState(seed)

    # Default model parameters calibrated to literature
    if model_params is None:
        model_params = {
            'base_accuracy_easy': 0.95,   # Heimdall: 94.5% single-pass
            'base_accuracy_hard': 0.55,   # Near chance for hard instances
            'max_accuracy_easy': 0.99,     # Ceiling for easy proofs
            'max_accuracy_hard': 0.75,     # Ceiling for hard proofs
            'lambda_scale': 2.0,           # Scale for convergence rate
            'noise_scale': 0.02,           # Noise in accuracy measurement
            'complexity_weights': {
                'log_length': 0.25,
                'log_width': 0.35,         # Width is strong predictor
                'log_depth': 0.15,
                'log_space': 0.25,         # Space predicts practical hardness
            }
        }

    # Compute normalized complexity
    features = compute_normalized_complexity(instance)

    # Compute weighted complexity score
    weights = model_params['complexity_weights']
    complexity_score = sum(
        weights.get(k, 0) * features.get(k, 0)
        for k in weights
    )

    # Normalize complexity to [0, 1] range (using sigmoid)
    normalized_complexity = 1 / (1 + np.exp(-0.5 * (complexity_score - 5)))

    # Model parameters as function of complexity
    p_0 = (model_params['base_accuracy_easy'] * (1 - normalized_complexity) +
           model_params['base_accuracy_hard'] * normalized_complexity)

    p_max = (model_params['max_accuracy_easy'] * (1 - normalized_complexity) +
             model_params['max_accuracy_hard'] * normalized_complexity)

    # Convergence rate: inversely proportional to complexity
    # Higher complexity -> slower convergence
    lam = model_params['lambda_scale'] / (1 + complexity_score)

    # Generate accuracy curve
    steps = np.arange(1, max_steps + 1)
    true_accuracy = p_max - (p_max - p_0) * np.exp(-lam * steps)

    # Simulate with noise (representing sampling variability)
    noise_std = model_params['noise_scale']
    observed_accuracy = np.zeros(max_steps)

    for t_idx, t in enumerate(steps):
        # Simulate n_trials independent verification attempts
        successes = rng.binomial(n_trials, true_accuracy[t_idx])
        observed_accuracy[t_idx] = successes / n_trials

    # Find convergence step: first step where accuracy is within epsilon of final
    epsilon = 0.01  # 1% of final accuracy
    final_acc = observed_accuracy[-1]
    convergence_step = max_steps
    for t in range(max_steps):
        if abs(observed_accuracy[t] - final_acc) < epsilon:
            convergence_step = t + 1
            break

    return ConvergenceResult(
        instance_name=instance.name,
        family=instance.family,
        accuracy_curve=observed_accuracy,
        convergence_step=convergence_step,
        final_accuracy=final_acc,
        convergence_rate=lam,
        complexity_features=features,
        base_accuracy=p_0,
        noise_std=noise_std,
    )


def self_consistency_accuracy(p: float, n_chains: int) -> float:
    """
    Compute majority vote accuracy from n_chains independent chains,
    each with individual accuracy p.

    P_maj = sum_{k > n/2} C(n,k) * p^k * (1-p)^{n-k}
    """
    from scipy.stats import binom
    threshold = n_chains // 2 + 1
    return 1 - binom.cdf(threshold - 1, n_chains, p)


def simulate_self_consistency(
    instance: ProofInstance,
    max_chains: int = 64,
    cot_steps: int = 10,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate self-consistency (majority voting) convergence.

    Returns accuracy as function of number of chains for a fixed CoT depth.
    """
    result = verification_accuracy_model(instance, max_steps=cot_steps, seed=seed)
    base_p = result.accuracy_curve[-1]  # accuracy at final CoT step

    chain_counts = np.arange(1, max_chains + 1, 2)  # odd numbers for clean majority
    accuracies = np.array([self_consistency_accuracy(base_p, n) for n in chain_counts])

    return chain_counts, accuracies


def run_full_simulation(
    instances: List[ProofInstance],
    max_steps: int = 20,
    n_trials: int = 200,
    seed: int = 42,
) -> List[ConvergenceResult]:
    """Run verification simulation for all proof instances."""
    results = []
    for i, inst in enumerate(instances):
        result = verification_accuracy_model(
            inst, max_steps=max_steps, n_trials=n_trials, seed=seed + i
        )
        results.append(result)
    return results


if __name__ == '__main__':
    from src.proof_generator import generate_dataset

    instances = generate_dataset()
    results = run_full_simulation(instances)

    print(f"Simulated {len(results)} instances")
    for family in ['tseitin', 'pigeonhole', 'pebbling', 'random_kcnf']:
        fam_results = [r for r in results if r.family == family]
        if fam_results:
            avg_conv = np.mean([r.convergence_step for r in fam_results])
            avg_rate = np.mean([r.convergence_rate for r in fam_results])
            avg_final = np.mean([r.final_accuracy for r in fam_results])
            print(f"  {family}: avg_conv_step={avg_conv:.1f}, avg_rate={avg_rate:.3f}, avg_final_acc={avg_final:.3f}")
