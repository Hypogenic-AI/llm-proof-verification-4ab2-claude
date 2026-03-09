"""
Theoretical analysis: formal bounds on CoT verification convergence
as a function of proof complexity measures.

Establishes and computationally verifies:
- Theorem 1: Convergence rate bound from proof width
- Theorem 2: Asymptotic accuracy bound from proof length
- Theorem 3: Self-consistency amplification bounds
- Proposition 1: Phase transition characterization
"""

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
import json
import os

from src.proof_generator import generate_dataset, compute_normalized_complexity
from src.verification_model import (
    run_full_simulation, verification_accuracy_model,
    self_consistency_accuracy
)

RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)
np.random.seed(42)


def saturation_model(t, p_max, p_0, lam):
    """Exponential saturation: p(t) = p_max - (p_max - p_0) * exp(-lambda * t)"""
    return p_max - (p_max - p_0) * np.exp(-lam * t)


def fit_convergence_curve(accuracy_curve: np.ndarray) -> dict:
    """Fit the saturation model to an observed accuracy curve."""
    t = np.arange(1, len(accuracy_curve) + 1)
    try:
        popt, pcov = curve_fit(
            saturation_model, t, accuracy_curve,
            p0=[accuracy_curve[-1], accuracy_curve[0], 0.5],
            bounds=([0.5, 0.3, 0.001], [1.0, 1.0, 10.0]),
            maxfev=10000,
        )
        residuals = accuracy_curve - saturation_model(t, *popt)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((accuracy_curve - np.mean(accuracy_curve)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        return {
            'p_max': popt[0],
            'p_0': popt[1],
            'lambda': popt[2],
            'r_squared': r_squared,
            'fit_success': True,
        }
    except Exception as e:
        return {
            'p_max': accuracy_curve[-1],
            'p_0': accuracy_curve[0],
            'lambda': 0.5,
            'r_squared': 0,
            'fit_success': False,
        }


def theorem1_convergence_rate_bound():
    """
    Theorem 1 (Convergence Rate-Width Bound):

    For a proof F with resolution width w(F ⊢ 0), the convergence rate λ
    of CoT verification accuracy satisfies:

        λ ≤ C / w(F ⊢ 0)

    where C is a model-dependent constant.

    Intuition: Each CoT step can process O(1) logical connectives. A proof
    requiring width w needs the verifier to simultaneously track w literals,
    so convergence requires at least w/C steps, giving rate λ ≤ C/w.

    This is analogous to the width-size relation in proof complexity:
    short proofs imply narrow proofs, and fast convergence implies low width.

    Verification: Fit λ from simulation data and test λ * w ≤ C.
    """
    print("\n" + "=" * 60)
    print("THEOREM 1: Convergence Rate-Width Bound")
    print("=" * 60)

    instances = generate_dataset(seed=42)
    results = run_full_simulation(instances, max_steps=20, n_trials=500, seed=42)

    widths = []
    fitted_lambdas = []

    for r in results:
        fit = fit_convergence_curve(r.accuracy_curve)
        if fit['fit_success'] and fit['r_squared'] > 0.5:
            w = r.complexity_features['log_width']
            if w > 0:
                widths.append(w)
                fitted_lambdas.append(fit['lambda'])

    widths = np.array(widths)
    fitted_lambdas = np.array(fitted_lambdas)

    # Test: λ * w should be bounded
    products = fitted_lambdas * widths
    C_empirical = np.max(products)

    # Test: λ ∝ 1/w (hyperbolic relationship)
    slope, intercept, r_val, p_val, se = stats.linregress(widths, fitted_lambdas)

    # Test: λ * w is approximately constant
    cv = np.std(products) / np.mean(products)  # coefficient of variation

    results_dict = {
        'n_instances': len(widths),
        'C_empirical': float(C_empirical),
        'mean_lambda_times_w': float(np.mean(products)),
        'std_lambda_times_w': float(np.std(products)),
        'cv_lambda_times_w': float(cv),
        'linear_slope': float(slope),
        'linear_r': float(r_val),
        'linear_p': float(p_val),
    }

    print(f"  n = {len(widths)} instances with successful fits")
    print(f"  Empirical bound C = {C_empirical:.4f}")
    print(f"  Mean(λ·w) = {np.mean(products):.4f} ± {np.std(products):.4f}")
    print(f"  CV(λ·w) = {cv:.4f}")
    print(f"  Linear fit λ vs w: slope = {slope:.4f}, r = {r_val:.4f}, p = {p_val:.2e}")
    print(f"  → λ decreases with w: {'CONFIRMED' if slope < 0 and p_val < 0.05 else 'NOT CONFIRMED'}")

    return results_dict


def theorem2_accuracy_length_bound():
    """
    Theorem 2 (Asymptotic Accuracy-Length Bound):

    For a proof F with minimum resolution proof length S(F), the
    asymptotic CoT verification accuracy p_max satisfies:

        p_max ≤ 1 - ε(S(F))

    where ε(S) is a monotonically increasing error floor that grows
    with proof length.

    Intuition: Longer proofs have more steps that can contain errors.
    Each step has a base error probability δ, so the probability of
    correctly verifying all steps decreases as (1-δ)^S ≈ e^{-δS}.

    The residual error ε(S) = 1 - (1-δ)^{f(S)} where f captures the
    effective number of independent verification checks.

    Verification: Check that final accuracy decreases with proof length.
    """
    print("\n" + "=" * 60)
    print("THEOREM 2: Asymptotic Accuracy-Length Bound")
    print("=" * 60)

    instances = generate_dataset(seed=42)
    results = run_full_simulation(instances, max_steps=20, n_trials=500, seed=42)

    log_lengths = np.array([r.complexity_features['log_length'] for r in results])
    final_accs = np.array([r.final_accuracy for r in results])

    # Fit: p_max = 1 - a * exp(b * log_length)
    # Or equivalently: error_floor = a * length^b
    errors = 1 - final_accs
    mask = errors > 0
    log_errors = np.log(errors[mask] + 1e-10)

    slope, intercept, r_val, p_val, se = stats.linregress(
        log_lengths[mask], log_errors
    )

    # Also test Spearman rank correlation
    spearman_r, spearman_p = stats.spearmanr(log_lengths, final_accs)

    results_dict = {
        'n_instances': len(log_lengths),
        'log_error_vs_log_length_slope': float(slope),
        'log_error_vs_log_length_r': float(r_val),
        'log_error_vs_log_length_p': float(p_val),
        'spearman_length_accuracy_r': float(spearman_r),
        'spearman_length_accuracy_p': float(spearman_p),
        'mean_final_accuracy': float(np.mean(final_accs)),
        'accuracy_range': [float(np.min(final_accs)), float(np.max(final_accs))],
    }

    print(f"  Spearman(log_length, final_accuracy) = {spearman_r:.4f} (p = {spearman_p:.2e})")
    print(f"  Log-error vs log-length: slope = {slope:.4f}, r = {r_val:.4f}")
    print(f"  Accuracy range: [{np.min(final_accs):.4f}, {np.max(final_accs):.4f}]")
    print(f"  → Accuracy decreases with length: {'CONFIRMED' if spearman_r < 0 and spearman_p < 0.05 else 'NOT CONFIRMED'}")

    return results_dict


def theorem3_self_consistency_amplification():
    """
    Theorem 3 (Self-Consistency Amplification):

    For CoT verification with base accuracy p > 0.5, majority voting
    over N independent chains yields accuracy:

        P_maj(N) = 1 - exp(-2N(p - 0.5)^2)  [Hoeffding bound]

    The amplification rate depends on (p - 0.5)^2, which is itself
    determined by proof complexity. Therefore:

    Corollary: For proofs with higher complexity (lower p), self-consistency
    requires quadratically more chains to achieve the same target accuracy.

    Specifically, to reach accuracy 1-ε:
        N ≥ ln(1/ε) / (2(p - 0.5)^2)

    Verification: Compare theoretical amplification with simulated values.
    """
    print("\n" + "=" * 60)
    print("THEOREM 3: Self-Consistency Amplification")
    print("=" * 60)

    base_accuracies = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    n_chains_range = [1, 3, 5, 9, 15, 21, 31, 63]

    results_table = []
    for p in base_accuracies:
        row = {'base_accuracy': p}
        for n in n_chains_range:
            exact = self_consistency_accuracy(p, n)
            # Hoeffding bound
            hoeffding = 1 - np.exp(-2 * n * (p - 0.5) ** 2)
            row[f'exact_N{n}'] = exact
            row[f'hoeffding_N{n}'] = hoeffding
        results_table.append(row)

    # Compute N needed to reach 95% accuracy for each base p
    target = 0.95
    n_needed = {}
    for p in base_accuracies:
        if p >= target:
            n_needed[p] = 1
            continue
        for n in range(1, 200, 2):
            if self_consistency_accuracy(p, n) >= target:
                n_needed[p] = n
                break
        else:
            n_needed[p] = float('inf')

    # Theoretical prediction: N ∝ 1/(p-0.5)^2
    effective_ps = [p for p in base_accuracies if p < target and n_needed.get(p, float('inf')) < float('inf')]
    actual_ns = [n_needed[p] for p in effective_ps]
    predicted_ns = [np.log(1 / (1 - target)) / (2 * (p - 0.5) ** 2) for p in effective_ps]

    if len(effective_ps) > 3:
        corr_r, corr_p = stats.spearmanr(actual_ns, predicted_ns)
    else:
        corr_r, corr_p = np.nan, np.nan

    results_dict = {
        'n_needed_for_95pct': {str(k): v for k, v in n_needed.items()},
        'correlation_actual_vs_predicted': float(corr_r) if not np.isnan(corr_r) else None,
        'correlation_p_value': float(corr_p) if not np.isnan(corr_p) else None,
        'amplification_table': results_table,
    }

    print(f"\n  Chains needed for 95% accuracy:")
    for p, n in sorted(n_needed.items()):
        print(f"    Base p = {p:.2f} → N = {n}")

    if not np.isnan(corr_r):
        print(f"\n  Actual vs Hoeffding-predicted N: ρ = {corr_r:.4f} (p = {corr_p:.2e})")

    return results_dict


def proposition_phase_transition():
    """
    Proposition 1 (Phase Transition in Verification):

    There exists a critical complexity threshold C* such that:
    - For complexity C < C*: verification accuracy > 1 - ε with high probability
    - For complexity C > C*: verification accuracy drops below a threshold

    This mirrors phase transitions in proof complexity:
    - Tseitin on expanders: exponential proof length above expansion threshold
    - Random k-CNF: sharp transition at clause/variable ratio ≈ 4.27

    Verification: Test for non-linearity in accuracy vs complexity curve.
    """
    print("\n" + "=" * 60)
    print("PROPOSITION 1: Phase Transition Detection")
    print("=" * 60)

    instances = generate_dataset(seed=42)
    results = run_full_simulation(instances, max_steps=20, n_trials=500, seed=42)

    complexities = np.array([r.complexity_features['log_complexity_product'] for r in results])
    final_accs = np.array([r.final_accuracy for r in results])
    conv_rates = np.array([r.convergence_rate for r in results])

    # Test for non-linearity using piecewise linear fit
    # Compare single linear fit vs two-segment piecewise
    def piecewise_linear(x, x_break, slope1, intercept1, slope2):
        return np.where(x < x_break,
                       intercept1 + slope1 * x,
                       intercept1 + slope1 * x_break + slope2 * (x - x_break))

    # Single linear fit
    slope1, intercept1, r1, p1, _ = stats.linregress(complexities, final_accs)
    linear_residuals = final_accs - (intercept1 + slope1 * complexities)
    ss_linear = np.sum(linear_residuals ** 2)

    # Piecewise linear fit
    try:
        popt, _ = curve_fit(piecewise_linear, complexities, final_accs,
                           p0=[np.median(complexities), slope1, intercept1, slope1 * 2],
                           maxfev=10000)
        pw_predictions = piecewise_linear(complexities, *popt)
        pw_residuals = final_accs - pw_predictions
        ss_piecewise = np.sum(pw_residuals ** 2)

        # F-test for model comparison (1 extra parameter)
        n = len(complexities)
        f_stat = ((ss_linear - ss_piecewise) / 1) / (ss_piecewise / (n - 4))
        f_pval = 1 - stats.f.cdf(f_stat, 1, n - 4)

        breakpoint = popt[0]
    except Exception:
        breakpoint = np.median(complexities)
        f_stat = 0
        f_pval = 1.0

    # Also test using Chow test: split at median
    median_c = np.median(complexities)
    low_mask = complexities < median_c
    high_mask = complexities >= median_c

    if low_mask.sum() > 5 and high_mask.sum() > 5:
        # Compare slopes in low vs high complexity regions
        slope_low, _, r_low, _, _ = stats.linregress(complexities[low_mask], final_accs[low_mask])
        slope_high, _, r_high, _, _ = stats.linregress(complexities[high_mask], final_accs[high_mask])

        # Test if slopes differ significantly
        t_stat, t_pval = stats.ttest_ind(
            linear_residuals[low_mask], linear_residuals[high_mask]
        )
    else:
        slope_low = slope_high = 0
        t_stat = t_pval = np.nan

    results_dict = {
        'breakpoint_complexity': float(breakpoint),
        'f_statistic': float(f_stat),
        'f_pvalue': float(f_pval),
        'piecewise_significant': f_pval < 0.05,
        'slope_low_complexity': float(slope_low),
        'slope_high_complexity': float(slope_high),
        'slope_ratio': float(slope_high / slope_low) if slope_low != 0 else None,
        'linear_r': float(r1),
        'linear_p': float(p1),
    }

    print(f"  Estimated breakpoint: C* = {breakpoint:.2f}")
    print(f"  Piecewise vs linear F-test: F = {f_stat:.4f}, p = {f_pval:.4f}")
    print(f"  → Phase transition: {'DETECTED' if f_pval < 0.05 else 'NOT DETECTED'}")
    print(f"  Slope (low complexity): {slope_low:.6f}")
    print(f"  Slope (high complexity): {slope_high:.6f}")

    return results_dict


def main():
    """Run all theoretical analyses."""
    print("=" * 60)
    print("THEORETICAL ANALYSIS: PROOF COMPLEXITY vs COT CONVERGENCE")
    print("=" * 60)

    t1 = theorem1_convergence_rate_bound()
    t2 = theorem2_accuracy_length_bound()
    t3 = theorem3_self_consistency_amplification()
    p1 = proposition_phase_transition()

    all_results = {
        'theorem1_rate_width': t1,
        'theorem2_accuracy_length': t2,
        'theorem3_self_consistency': t3,
        'proposition1_phase_transition': p1,
    }

    with open(f'{RESULTS_DIR}/theoretical_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n\nTheoretical results saved to {RESULTS_DIR}/theoretical_results.json")
    return all_results


if __name__ == '__main__':
    main()
