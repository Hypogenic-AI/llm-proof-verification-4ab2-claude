"""
Statistical analysis and visualization for proof complexity vs CoT convergence.

Performs:
1. Correlation analysis between complexity measures and convergence metrics
2. Regression modeling to predict convergence from complexity
3. Phase transition detection at critical complexity thresholds
4. Comprehensive visualizations
"""

import numpy as np
import json
import os
from scipy import stats
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import List, Dict, Tuple

from src.proof_generator import generate_dataset, compute_normalized_complexity, ProofInstance
from src.verification_model import (
    run_full_simulation, ConvergenceResult,
    simulate_self_consistency, verification_accuracy_model
)

# Reproducibility
np.random.seed(42)

RESULTS_DIR = 'results'
FIGURES_DIR = 'figures'
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)


def extract_data_matrix(results: List[ConvergenceResult]) -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
    """
    Extract complexity features and convergence metrics into matrices.

    Returns:
        X: (n_instances, n_features) complexity features
        Y: (n_instances, n_metrics) convergence metrics
        feature_names: names of complexity features
        metric_names: names of convergence metrics
    """
    feature_names = [
        'log_length', 'log_width', 'log_depth', 'log_space',
        'length_per_var', 'width_per_var', 'depth_per_var', 'space_per_var',
        'clause_var_ratio', 'formula_width', 'log_complexity_product',
    ]

    metric_names = ['convergence_step', 'convergence_rate', 'final_accuracy']

    n = len(results)
    X = np.zeros((n, len(feature_names)))
    Y = np.zeros((n, len(metric_names)))

    for i, r in enumerate(results):
        for j, f in enumerate(feature_names):
            X[i, j] = r.complexity_features.get(f, 0)
        Y[i, 0] = r.convergence_step
        Y[i, 1] = r.convergence_rate
        Y[i, 2] = r.final_accuracy

    return X, Y, feature_names, metric_names


def compute_correlations(X, Y, feature_names, metric_names):
    """Compute Pearson and Spearman correlations between all feature-metric pairs."""
    results = {}

    for j, metric in enumerate(metric_names):
        results[metric] = {}
        for i, feature in enumerate(feature_names):
            x = X[:, i]
            y = Y[:, j]

            # Remove NaN/Inf
            mask = np.isfinite(x) & np.isfinite(y)
            x, y = x[mask], y[mask]

            if len(x) < 5:
                continue

            pearson_r, pearson_p = stats.pearsonr(x, y)
            spearman_r, spearman_p = stats.spearmanr(x, y)

            results[metric][feature] = {
                'pearson_r': pearson_r,
                'pearson_p': pearson_p,
                'spearman_r': spearman_r,
                'spearman_p': spearman_p,
                'n': len(x),
            }

    return results


def run_regression_analysis(X, Y, feature_names, metric_names):
    """Multiple regression: predict convergence metrics from complexity features."""
    from numpy.linalg import lstsq

    results = {}

    for j, metric in enumerate(metric_names):
        y = Y[:, j]
        mask = np.isfinite(y)

        # Add intercept
        X_with_intercept = np.column_stack([np.ones(mask.sum()), X[mask]])
        y_clean = y[mask]

        # Ordinary least squares
        coeffs, residuals, rank, sv = lstsq(X_with_intercept, y_clean, rcond=None)

        # Predictions and R²
        y_pred = X_with_intercept @ coeffs
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # Feature importance (absolute standardized coefficients)
        std_x = np.std(X[mask], axis=0)
        std_y = np.std(y_clean)
        standardized_coeffs = coeffs[1:] * std_x / std_y if std_y > 0 else coeffs[1:]

        results[metric] = {
            'r_squared': r_squared,
            'coefficients': dict(zip(feature_names, coeffs[1:].tolist())),
            'intercept': coeffs[0],
            'standardized_coefficients': dict(zip(feature_names, standardized_coeffs.tolist())),
            'n': int(mask.sum()),
        }

    return results


def detect_phase_transitions(results: List[ConvergenceResult], n_bins: int = 5):
    """
    Detect phase transitions: sharp changes in verification accuracy
    as complexity increases.
    """
    # Use log_complexity_product as the composite measure
    complexities = [r.complexity_features['log_complexity_product'] for r in results]
    final_accs = [r.final_accuracy for r in results]
    conv_rates = [r.convergence_rate for r in results]

    # Sort by complexity
    sorted_idx = np.argsort(complexities)
    sorted_complex = np.array(complexities)[sorted_idx]
    sorted_acc = np.array(final_accs)[sorted_idx]
    sorted_rate = np.array(conv_rates)[sorted_idx]

    # Bin by complexity
    bin_edges = np.linspace(sorted_complex.min(), sorted_complex.max(), n_bins + 1)
    bin_results = []

    for b in range(n_bins):
        mask = (sorted_complex >= bin_edges[b]) & (sorted_complex < bin_edges[b + 1])
        if b == n_bins - 1:
            mask = (sorted_complex >= bin_edges[b]) & (sorted_complex <= bin_edges[b + 1])

        if mask.sum() < 2:
            continue

        bin_results.append({
            'bin': b,
            'complexity_range': (float(bin_edges[b]), float(bin_edges[b + 1])),
            'mean_complexity': float(sorted_complex[mask].mean()),
            'mean_accuracy': float(sorted_acc[mask].mean()),
            'std_accuracy': float(sorted_acc[mask].std()),
            'mean_conv_rate': float(sorted_rate[mask].mean()),
            'std_conv_rate': float(sorted_rate[mask].std()),
            'n': int(mask.sum()),
        })

    # Detect transitions: largest accuracy drop between adjacent bins
    transitions = []
    for i in range(len(bin_results) - 1):
        acc_drop = bin_results[i]['mean_accuracy'] - bin_results[i + 1]['mean_accuracy']
        rate_drop = bin_results[i]['mean_conv_rate'] - bin_results[i + 1]['mean_conv_rate']
        transitions.append({
            'from_bin': i,
            'to_bin': i + 1,
            'accuracy_drop': float(acc_drop),
            'rate_drop': float(rate_drop),
            'threshold_complexity': float(bin_results[i + 1]['complexity_range'][0]),
        })

    return bin_results, transitions


def per_family_analysis(results: List[ConvergenceResult]):
    """Analyze convergence patterns within each formula family."""
    families = defaultdict(list)
    for r in results:
        families[r.family].append(r)

    family_stats = {}
    for family, fam_results in families.items():
        conv_steps = [r.convergence_step for r in fam_results]
        conv_rates = [r.convergence_rate for r in fam_results]
        final_accs = [r.final_accuracy for r in fam_results]

        # Within-family correlation: log_width vs convergence_rate
        widths = [r.complexity_features['log_width'] for r in fam_results]
        if len(widths) > 3:
            width_rate_corr = stats.spearmanr(widths, conv_rates)
        else:
            width_rate_corr = (np.nan, np.nan)

        family_stats[family] = {
            'n': len(fam_results),
            'conv_step_mean': float(np.mean(conv_steps)),
            'conv_step_std': float(np.std(conv_steps)),
            'conv_rate_mean': float(np.mean(conv_rates)),
            'conv_rate_std': float(np.std(conv_rates)),
            'final_acc_mean': float(np.mean(final_accs)),
            'final_acc_std': float(np.std(final_accs)),
            'width_rate_spearman_r': float(width_rate_corr[0]) if not np.isnan(width_rate_corr[0]) else None,
            'width_rate_spearman_p': float(width_rate_corr[1]) if not np.isnan(width_rate_corr[1]) else None,
        }

    return family_stats


# ────────────────────────────────────────────
# Visualization functions
# ────────────────────────────────────────────

def plot_convergence_curves(results: List[ConvergenceResult], instances: List[ProofInstance]):
    """Plot convergence curves grouped by complexity class."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    families = ['tseitin', 'pigeonhole', 'pebbling', 'random_kcnf']
    family_labels = ['Tseitin Formulas', 'Pigeonhole Principle', 'Pebbling Formulas', 'Random 3-CNF']

    for idx, (family, label) in enumerate(zip(families, family_labels)):
        ax = axes[idx // 2][idx % 2]
        fam_results = [r for r in results if r.family == family]

        if not fam_results:
            ax.set_title(f'{label} (no data)')
            continue

        # Sort by complexity (log_complexity_product)
        fam_results.sort(key=lambda r: r.complexity_features['log_complexity_product'])

        # Color by complexity
        complexities = [r.complexity_features['log_complexity_product'] for r in fam_results]
        cmin, cmax = min(complexities), max(complexities)

        # Plot subset of curves (every other for readability)
        n_show = min(15, len(fam_results))
        indices = np.linspace(0, len(fam_results) - 1, n_show, dtype=int)

        for i in indices:
            r = fam_results[i]
            c_norm = (r.complexity_features['log_complexity_product'] - cmin) / (cmax - cmin + 1e-10)
            color = plt.cm.viridis(1 - c_norm)  # darker = more complex
            ax.plot(range(1, len(r.accuracy_curve) + 1), r.accuracy_curve,
                    color=color, alpha=0.7, linewidth=1.5)

        ax.set_xlabel('CoT Steps')
        ax.set_ylabel('Verification Accuracy')
        ax.set_title(label)
        ax.set_ylim(0.4, 1.0)
        ax.grid(True, alpha=0.3)

        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(cmin, cmax))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label('Complexity (log product)')

    plt.tight_layout()
    plt.savefig(f'{FIGURES_DIR}/convergence_curves.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_correlation_heatmap(correlations: Dict):
    """Plot heatmap of Spearman correlations between features and metrics."""
    metrics = list(correlations.keys())
    features = list(next(iter(correlations.values())).keys())

    # Build correlation matrix
    r_matrix = np.zeros((len(features), len(metrics)))
    p_matrix = np.zeros((len(features), len(metrics)))

    for j, metric in enumerate(metrics):
        for i, feature in enumerate(features):
            if feature in correlations[metric]:
                r_matrix[i, j] = correlations[metric][feature]['spearman_r']
                p_matrix[i, j] = correlations[metric][feature]['spearman_p']

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(r_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')

    # Labels
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels(['Conv. Step', 'Conv. Rate', 'Final Accuracy'], rotation=30, ha='right')
    ax.set_yticks(range(len(features)))
    ax.set_yticklabels([f.replace('_', ' ') for f in features])

    # Annotate with r values and significance stars
    for i in range(len(features)):
        for j in range(len(metrics)):
            r = r_matrix[i, j]
            p = p_matrix[i, j]
            stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
            text = f'{r:.2f}{stars}'
            color = 'white' if abs(r) > 0.5 else 'black'
            ax.text(j, i, text, ha='center', va='center', color=color, fontsize=8)

    plt.colorbar(im, label='Spearman ρ')
    ax.set_title('Correlation: Proof Complexity vs CoT Convergence')
    plt.tight_layout()
    plt.savefig(f'{FIGURES_DIR}/correlation_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_key_relationships(results: List[ConvergenceResult]):
    """Plot the key scatter plots: complexity measures vs convergence metrics."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    # Key feature-metric pairs
    pairs = [
        ('log_width', 'convergence_rate', 'Log Width', 'Convergence Rate'),
        ('log_space', 'convergence_rate', 'Log Space', 'Convergence Rate'),
        ('log_length', 'convergence_rate', 'Log Length', 'Convergence Rate'),
        ('log_width', 'final_accuracy', 'Log Width', 'Final Accuracy'),
        ('log_complexity_product', 'convergence_step', 'Log Complexity Product', 'Convergence Step'),
        ('log_complexity_product', 'final_accuracy', 'Log Complexity Product', 'Final Accuracy'),
    ]

    family_colors = {
        'tseitin': '#e41a1c',
        'pigeonhole': '#377eb8',
        'pebbling': '#4daf4a',
        'random_kcnf': '#ff7f00',
    }

    for idx, (feat, metric, xlabel, ylabel) in enumerate(pairs):
        ax = axes[idx // 3][idx % 3]

        for family, color in family_colors.items():
            fam_results = [r for r in results if r.family == family]
            x = [r.complexity_features[feat] for r in fam_results]
            y_vals = [getattr(r, metric) for r in fam_results]
            ax.scatter(x, y_vals, c=color, alpha=0.6, s=30, label=family)

        # Add regression line
        all_x = [r.complexity_features[feat] for r in results]
        all_y = [getattr(r, metric) for r in results]
        if len(all_x) > 5:
            slope, intercept, r_val, p_val, se = stats.linregress(all_x, all_y)
            x_line = np.linspace(min(all_x), max(all_x), 100)
            ax.plot(x_line, slope * x_line + intercept, 'k--', alpha=0.5,
                    label=f'r={r_val:.2f}, p={p_val:.2e}')

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    plt.suptitle('Proof Complexity Measures vs CoT Convergence Metrics', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'{FIGURES_DIR}/key_relationships.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_phase_transitions(bin_results, transitions):
    """Plot accuracy and convergence rate as function of complexity bins."""
    if len(bin_results) < 2:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    complexities = [b['mean_complexity'] for b in bin_results]
    accs = [b['mean_accuracy'] for b in bin_results]
    acc_errs = [b['std_accuracy'] for b in bin_results]
    rates = [b['mean_conv_rate'] for b in bin_results]
    rate_errs = [b['std_conv_rate'] for b in bin_results]

    ax1.errorbar(complexities, accs, yerr=acc_errs, fmt='o-', capsize=5,
                 color='#2c7bb6', linewidth=2, markersize=8)
    ax1.set_xlabel('Mean Complexity (log product)')
    ax1.set_ylabel('Mean Final Accuracy')
    ax1.set_title('Verification Accuracy vs Complexity')
    ax1.grid(True, alpha=0.3)

    ax2.errorbar(complexities, rates, yerr=rate_errs, fmt='s-', capsize=5,
                 color='#d7191c', linewidth=2, markersize=8)
    ax2.set_xlabel('Mean Complexity (log product)')
    ax2.set_ylabel('Mean Convergence Rate')
    ax2.set_title('Convergence Rate vs Complexity')
    ax2.grid(True, alpha=0.3)

    # Mark largest transition
    if transitions:
        max_trans = max(transitions, key=lambda t: abs(t['accuracy_drop']))
        threshold = max_trans['threshold_complexity']
        ax1.axvline(threshold, color='red', linestyle=':', alpha=0.7,
                    label=f'Threshold: {threshold:.1f}')
        ax2.axvline(threshold, color='red', linestyle=':', alpha=0.7,
                    label=f'Threshold: {threshold:.1f}')
        ax1.legend()
        ax2.legend()

    plt.tight_layout()
    plt.savefig(f'{FIGURES_DIR}/phase_transitions.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_self_consistency(instances: List[ProofInstance]):
    """Plot self-consistency convergence for instances of different complexity."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Select instances spanning complexity range
    complexities = [compute_normalized_complexity(inst)['log_complexity_product'] for inst in instances]
    sorted_idx = np.argsort(complexities)

    # Pick 5 representative instances
    n_show = 5
    pick_idx = np.linspace(0, len(sorted_idx) - 1, n_show, dtype=int)

    colors = plt.cm.viridis(np.linspace(0.2, 0.8, n_show))

    for i, idx in enumerate(pick_idx):
        inst = instances[sorted_idx[idx]]
        chains, accs = simulate_self_consistency(inst, max_chains=64)
        c = complexities[sorted_idx[idx]]
        ax.plot(chains, accs, color=colors[i], linewidth=2,
                label=f'{inst.family} (C={c:.1f})')

    ax.set_xlabel('Number of Independent Chains (Self-Consistency)')
    ax.set_ylabel('Majority Vote Accuracy')
    ax.set_title('Self-Consistency Convergence by Proof Complexity')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0.5, 1.02)

    plt.tight_layout()
    plt.savefig(f'{FIGURES_DIR}/self_consistency.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_family_comparison(family_stats: Dict):
    """Bar chart comparing convergence metrics across formula families."""
    families = list(family_stats.keys())
    x = np.arange(len(families))
    width = 0.25

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

    # Convergence step
    means = [family_stats[f]['conv_step_mean'] for f in families]
    stds = [family_stats[f]['conv_step_std'] for f in families]
    ax1.bar(x, means, width, yerr=stds, capsize=5, color='#377eb8')
    ax1.set_xticks(x)
    ax1.set_xticklabels(families, rotation=30, ha='right')
    ax1.set_ylabel('Convergence Step')
    ax1.set_title('Steps to Convergence')
    ax1.grid(True, alpha=0.3, axis='y')

    # Convergence rate
    means = [family_stats[f]['conv_rate_mean'] for f in families]
    stds = [family_stats[f]['conv_rate_std'] for f in families]
    ax2.bar(x, means, width, yerr=stds, capsize=5, color='#e41a1c')
    ax2.set_xticks(x)
    ax2.set_xticklabels(families, rotation=30, ha='right')
    ax2.set_ylabel('Convergence Rate (λ)')
    ax2.set_title('Convergence Rate')
    ax2.grid(True, alpha=0.3, axis='y')

    # Final accuracy
    means = [family_stats[f]['final_acc_mean'] for f in families]
    stds = [family_stats[f]['final_acc_std'] for f in families]
    ax3.bar(x, means, width, yerr=stds, capsize=5, color='#4daf4a')
    ax3.set_xticks(x)
    ax3.set_xticklabels(families, rotation=30, ha='right')
    ax3.set_ylabel('Final Accuracy')
    ax3.set_title('Asymptotic Accuracy')
    ax3.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Verification Metrics by Formula Family', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'{FIGURES_DIR}/family_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()


def main():
    """Run the complete analysis pipeline."""
    print("=" * 60)
    print("PROOF COMPLEXITY vs CoT CONVERGENCE ANALYSIS")
    print("=" * 60)

    # Phase 1: Generate data
    print("\n[1/6] Generating proof instances...")
    instances = generate_dataset(seed=42)
    print(f"  Generated {len(instances)} instances across 4 families")

    # Phase 2: Run simulation
    print("\n[2/6] Running verification convergence simulation...")
    results = run_full_simulation(instances, max_steps=20, n_trials=200, seed=42)
    print(f"  Simulated {len(results)} convergence curves")

    # Phase 3: Extract data matrices
    print("\n[3/6] Computing correlations...")
    X, Y, feature_names, metric_names = extract_data_matrix(results)

    # Correlation analysis
    correlations = compute_correlations(X, Y, feature_names, metric_names)

    # Print top correlations
    print("\n  Top Spearman correlations with convergence_rate:")
    rate_corrs = correlations['convergence_rate']
    sorted_feats = sorted(rate_corrs.keys(),
                          key=lambda f: abs(rate_corrs[f]['spearman_r']),
                          reverse=True)
    for f in sorted_feats[:5]:
        r = rate_corrs[f]['spearman_r']
        p = rate_corrs[f]['spearman_p']
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
        print(f"    {f:25s}: ρ = {r:+.4f}  (p = {p:.2e}) {sig}")

    # Phase 4: Regression analysis
    print("\n[4/6] Running regression analysis...")
    regression = run_regression_analysis(X, Y, feature_names, metric_names)
    for metric, reg in regression.items():
        print(f"  {metric}: R² = {reg['r_squared']:.4f}")

    # Phase 5: Phase transition detection
    print("\n[5/6] Detecting phase transitions...")
    bin_results, transitions = detect_phase_transitions(results, n_bins=6)
    if transitions:
        max_trans = max(transitions, key=lambda t: abs(t['accuracy_drop']))
        print(f"  Largest accuracy drop: {max_trans['accuracy_drop']:.4f} at complexity threshold {max_trans['threshold_complexity']:.2f}")

    # Per-family analysis
    family_stats = per_family_analysis(results)

    # Phase 6: Visualizations
    print("\n[6/6] Generating visualizations...")
    plot_convergence_curves(results, instances)
    plot_correlation_heatmap(correlations)
    plot_key_relationships(results)
    plot_phase_transitions(bin_results, transitions)
    plot_self_consistency(instances)
    plot_family_comparison(family_stats)
    print(f"  Saved plots to {FIGURES_DIR}/")

    # Save all results
    all_results = {
        'correlations': correlations,
        'regression': regression,
        'phase_transitions': {
            'bins': bin_results,
            'transitions': transitions,
        },
        'family_stats': family_stats,
        'summary': {
            'n_instances': len(instances),
            'n_families': 4,
            'families': list(family_stats.keys()),
        }
    }

    with open(f'{RESULTS_DIR}/analysis_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n  Full results saved to {RESULTS_DIR}/analysis_results.json")
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    return all_results


if __name__ == '__main__':
    main()
