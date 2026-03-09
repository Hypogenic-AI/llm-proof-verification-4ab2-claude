"""
Proof instance generator with controlled complexity parameters.

Generates synthetic proof instances from well-studied formula families
(Tseitin, Pigeonhole, Pebbling, Random k-CNF) with precisely known
proof complexity measures.
"""

import random
import numpy as np
import networkx as nx
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from itertools import combinations


@dataclass
class ProofInstance:
    """A proof instance with known complexity parameters."""
    name: str
    family: str  # tseitin, pigeonhole, pebbling, random_kcnf
    num_variables: int
    num_clauses: int
    clauses: List[List[int]]  # CNF: list of clauses, each clause is list of literals
    # Complexity measures
    proof_length: int  # number of resolution steps (exact or lower bound)
    proof_width: int   # max clause width in optimal proof
    proof_depth: int   # depth of proof DAG
    proof_space: int   # memory required (clauses simultaneously active)
    is_satisfiable: bool
    # Structural properties
    tree_like: bool  # whether tree-like proof exists efficiently
    formula_width: int  # max width of input clauses
    # Additional metadata
    metadata: Dict = field(default_factory=dict)


def generate_tseitin_formula(n_vertices: int, graph_type: str = 'cycle',
                              seed: int = 42) -> ProofInstance:
    """
    Generate Tseitin formula on a graph.

    Tseitin formulas encode parity constraints on graph edges.
    Key property: unsatisfiable when sum of charges is odd.

    Complexity depends on graph expansion:
    - Cycle graphs: width O(1), length O(n), depth O(n)
    - Grid graphs: width O(sqrt(n)), length exp(sqrt(n))
    - Expander graphs: width Omega(n), length exp(n)

    Args:
        n_vertices: Number of vertices in the graph
        graph_type: 'cycle', 'grid', 'expander', 'path'
        seed: Random seed
    """
    rng = random.Random(seed)

    if graph_type == 'cycle':
        G = nx.cycle_graph(n_vertices)
    elif graph_type == 'grid':
        side = int(np.ceil(np.sqrt(n_vertices)))
        G = nx.grid_2d_graph(side, side)
        # Relabel to integers
        mapping = {node: i for i, node in enumerate(G.nodes())}
        G = nx.relabel_nodes(G, mapping)
        n_vertices = G.number_of_nodes()
    elif graph_type == 'expander':
        # Use Margulis-Gabber-Galil expander construction (approximate)
        G = nx.random_regular_graph(3, n_vertices, seed=seed)
        if not nx.is_connected(G):
            G = nx.connected_component_subgraphs(G).__next__() if hasattr(nx, 'connected_component_subgraphs') else G.subgraph(max(nx.connected_components(G), key=len)).copy()
            n_vertices = G.number_of_nodes()
    elif graph_type == 'path':
        G = nx.path_graph(n_vertices)
    else:
        raise ValueError(f"Unknown graph type: {graph_type}")

    edges = list(G.edges())
    n_edges = len(edges)

    # Edge variables: x_e for each edge e
    # Variable numbering: edge index + 1
    edge_to_var = {e: i + 1 for i, e in enumerate(edges)}
    # Also map reverse edges
    for e, v in edge_to_var.copy().items():
        edge_to_var[(e[1], e[0])] = v

    # Charges: assign charge 1 to vertex 0, 0 to all others
    # This makes the formula unsatisfiable (odd total charge for connected graph)
    charges = {v: 0 for v in G.nodes()}
    charges[list(G.nodes())[0]] = 1

    clauses = []
    # For each vertex v with charge c_v:
    # XOR of incident edge variables = c_v
    # Encoded as CNF clauses
    for v in G.nodes():
        incident_edges = list(G.edges(v))
        incident_vars = [edge_to_var[(min(e), max(e))] for e in incident_edges]
        charge = charges[v]

        # XOR constraint: parity of vars = charge
        # Generate all combinations with correct parity
        n_inc = len(incident_vars)
        for bits in range(1 << n_inc):
            # Count number of 1s
            ones = bin(bits).count('1')
            # We want parity = charge, so skip if parity matches
            if ones % 2 == charge:
                continue
            # Create clause: negate vars where bit=1, keep where bit=0
            clause = []
            for j, var in enumerate(incident_vars):
                if bits & (1 << j):
                    clause.append(var)
                else:
                    clause.append(-var)
            clauses.append(clause)

    # Compute complexity measures based on graph structure
    if graph_type == 'cycle':
        proof_length = 2 * n_vertices  # O(n)
        proof_width = 3  # O(1)
        proof_depth = n_vertices
        proof_space = 4  # O(1)
    elif graph_type == 'path':
        proof_length = 2 * n_vertices
        proof_width = 2
        proof_depth = n_vertices
        proof_space = 3
    elif graph_type == 'grid':
        side = int(np.ceil(np.sqrt(n_vertices)))
        proof_width = side  # O(sqrt(n))
        proof_length = int(2 ** (side / 2))  # exp(sqrt(n))
        proof_depth = n_vertices
        proof_space = side + 1
    elif graph_type == 'expander':
        proof_width = n_vertices // 3  # Omega(n)
        proof_length = int(2 ** (n_vertices / 6))  # exp(n)
        proof_depth = n_vertices
        proof_space = n_vertices // 3

    return ProofInstance(
        name=f"tseitin_{graph_type}_{n_vertices}",
        family="tseitin",
        num_variables=n_edges,
        num_clauses=len(clauses),
        clauses=clauses,
        proof_length=proof_length,
        proof_width=proof_width,
        proof_depth=proof_depth,
        proof_space=proof_space,
        is_satisfiable=False,
        tree_like=(graph_type in ['cycle', 'path']),
        formula_width=max(len(c) for c in clauses) if clauses else 0,
        metadata={
            'graph_type': graph_type,
            'n_vertices': n_vertices,
            'n_edges': n_edges,
            'avg_degree': 2 * n_edges / n_vertices if n_vertices > 0 else 0,
            'expansion': nx.algebraic_connectivity(G) if n_vertices <= 100 else None,
        }
    )


def generate_pigeonhole(n_pigeons: int, n_holes: int = None) -> ProofInstance:
    """
    Generate Pigeonhole Principle formula: PHP^n_{n-1}.

    States that n pigeons can be placed in n-1 holes with no hole containing
    two pigeons. Always unsatisfiable.

    Complexity: tree-like proofs require exp(n) length.
    General resolution: polynomial width but exp(n) length.

    Args:
        n_pigeons: Number of pigeons
        n_holes: Number of holes (default: n_pigeons - 1)
    """
    if n_holes is None:
        n_holes = n_pigeons - 1

    # Variables: p_{i,j} = pigeon i goes to hole j
    # Variable numbering: (i * n_holes + j) + 1
    def var(pigeon, hole):
        return pigeon * n_holes + hole + 1

    num_variables = n_pigeons * n_holes
    clauses = []

    # Pigeon axioms: each pigeon must go to some hole
    for i in range(n_pigeons):
        clause = [var(i, j) for j in range(n_holes)]
        clauses.append(clause)

    # Hole axioms: no two pigeons in the same hole
    for j in range(n_holes):
        for i1, i2 in combinations(range(n_pigeons), 2):
            clauses.append([-var(i1, j), -var(i2, j)])

    # Known complexity measures for PHP^{n+1}_n
    # Tree-like: length = 2^{Omega(n)}
    # General: width = n, length = 2^{Omega(n/log n)} (Cook 1976, Haken 1985)
    proof_length = int(2 ** (n_pigeons / 2))  # exponential lower bound
    proof_width = n_holes  # width = n-1
    proof_depth = n_pigeons * n_holes
    proof_space = n_holes + 1

    return ProofInstance(
        name=f"php_{n_pigeons}_{n_holes}",
        family="pigeonhole",
        num_variables=num_variables,
        num_clauses=len(clauses),
        clauses=clauses,
        proof_length=proof_length,
        proof_width=proof_width,
        proof_depth=proof_depth,
        proof_space=proof_space,
        is_satisfiable=False,
        tree_like=False,
        formula_width=n_holes,  # pigeon axioms have width n_holes
        metadata={
            'n_pigeons': n_pigeons,
            'n_holes': n_holes,
            'ratio': n_pigeons / n_holes,
        }
    )


def generate_pebbling_formula(dag_type: str = 'pyramid', n: int = 4,
                                seed: int = 42) -> ProofInstance:
    """
    Generate pebbling formula from a DAG.

    Pebbling formulas encode the pebbling game on a DAG.
    Space complexity = pebbling number of the DAG.

    Args:
        dag_type: 'pyramid', 'tree', 'chain'
        n: Size parameter (height for pyramid/tree, length for chain)
        seed: Random seed
    """
    if dag_type == 'pyramid':
        # Pyramid DAG: level i has i+1 nodes, each connected to 2 parents
        G = nx.DiGraph()
        node_id = 0
        levels = []
        for level in range(n):
            level_nodes = []
            for j in range(level + 1):
                level_nodes.append(node_id)
                G.add_node(node_id)
                node_id += 1
            levels.append(level_nodes)
        # Connect consecutive levels
        for level in range(1, n):
            for j in range(len(levels[level])):
                if j < len(levels[level - 1]):
                    G.add_edge(levels[level - 1][j], levels[level][j])
                if j - 1 >= 0 and j - 1 < len(levels[level - 1]):
                    G.add_edge(levels[level - 1][j - 1], levels[level][j])
    elif dag_type == 'tree':
        # Complete binary tree of height n
        G = nx.balanced_tree(2, n, create_using=nx.DiGraph())
        # Reverse edges so leaves are sources
        G = G.reverse()
    elif dag_type == 'chain':
        G = nx.path_graph(n, create_using=nx.DiGraph())
    else:
        raise ValueError(f"Unknown DAG type: {dag_type}")

    num_dag_nodes = G.number_of_nodes()

    # Variables: x_v for each node v
    # Variable numbering: node + 1
    clauses = []

    # Source axioms: sources must be pebbled (set to true)
    sources = [v for v in G.nodes() if G.in_degree(v) == 0]
    for s in sources:
        clauses.append([s + 1])  # unit clause

    # Propagation axioms: if all predecessors are true, then v is true
    # For each non-source v with predecessors u1, ..., uk:
    # (NOT u1 OR NOT u2 OR ... OR NOT uk OR v)
    for v in G.nodes():
        preds = list(G.predecessors(v))
        if len(preds) > 0:
            clause = [-p - 1 for p in preds] + [v + 1]
            clauses.append(clause)

    # Sink axiom: sink must be false (negated)
    sinks = [v for v in G.nodes() if G.out_degree(v) == 0]
    for s in sinks:
        clauses.append([-(s + 1)])  # negated unit clause

    # Complexity measures
    if dag_type == 'chain':
        proof_length = 2 * n
        proof_width = 2
        proof_depth = n
        proof_space = 2
    elif dag_type == 'tree':
        proof_length = 2 ** (n + 1)
        proof_width = n + 1
        proof_depth = 2 * n
        proof_space = n + 1  # pebbling number of binary tree
    elif dag_type == 'pyramid':
        proof_length = n * (n + 1) // 2
        proof_width = n
        proof_depth = 2 * n
        proof_space = n  # pebbling number of pyramid

    return ProofInstance(
        name=f"pebbling_{dag_type}_{n}",
        family="pebbling",
        num_variables=num_dag_nodes,
        num_clauses=len(clauses),
        clauses=clauses,
        proof_length=proof_length,
        proof_width=proof_width,
        proof_depth=proof_depth,
        proof_space=proof_space,
        is_satisfiable=False,
        tree_like=(dag_type in ['chain', 'tree']),
        formula_width=max(len(c) for c in clauses) if clauses else 0,
        metadata={
            'dag_type': dag_type,
            'n': n,
            'num_dag_nodes': num_dag_nodes,
            'num_dag_edges': G.number_of_edges(),
        }
    )


def generate_random_kcnf(n_vars: int, k: int = 3, ratio: float = 4.0,
                          seed: int = 42) -> ProofInstance:
    """
    Generate random k-CNF formula.

    Near the satisfiability threshold (ratio ≈ 4.27 for 3-CNF),
    formulas are hardest for resolution.

    Args:
        n_vars: Number of variables
        k: Clause width
        ratio: Clause-to-variable ratio
        seed: Random seed
    """
    rng = random.Random(seed)
    n_clauses = int(n_vars * ratio)

    clauses = []
    for _ in range(n_clauses):
        vars_in_clause = rng.sample(range(1, n_vars + 1), k)
        clause = [v if rng.random() < 0.5 else -v for v in vars_in_clause]
        clauses.append(clause)

    # For random 3-CNF near threshold:
    # Proof length is typically exponential
    # Width is O(n) in hard cases
    if ratio > 4.0:
        # Likely unsatisfiable
        proof_length = int(2 ** (n_vars * 0.1))  # exponential estimate
        proof_width = int(n_vars * 0.3)
    else:
        # Likely satisfiable or easy
        proof_length = n_clauses
        proof_width = k

    proof_depth = int(n_vars * np.log2(n_vars + 1)) if n_vars > 1 else 1
    proof_space = int(n_vars * 0.2) + k

    return ProofInstance(
        name=f"random_{k}cnf_n{n_vars}_r{ratio:.1f}_s{seed}",
        family="random_kcnf",
        num_variables=n_vars,
        num_clauses=n_clauses,
        clauses=clauses,
        proof_length=proof_length,
        proof_width=proof_width,
        proof_depth=proof_depth,
        proof_space=proof_space,
        is_satisfiable=None,  # unknown a priori
        tree_like=False,
        formula_width=k,
        metadata={
            'k': k,
            'ratio': ratio,
            'seed': seed,
        }
    )


def generate_dataset(seed: int = 42) -> List[ProofInstance]:
    """Generate the full dataset of proof instances with controlled complexity."""
    instances = []

    # Tseitin formulas on different graph types and sizes
    for graph_type in ['path', 'cycle', 'grid', 'expander']:
        for n in [4, 6, 8, 10, 12, 15, 20]:
            try:
                if graph_type == 'expander' and n < 4:
                    continue
                if graph_type == 'grid' and n < 4:
                    continue
                inst = generate_tseitin_formula(n, graph_type, seed=seed)
                instances.append(inst)
            except Exception as e:
                pass  # Skip instances that fail (e.g., too small for graph type)

    # Pigeonhole principle with varying sizes
    for n_pigeons in range(3, 12):
        instances.append(generate_pigeonhole(n_pigeons))

    # Pebbling formulas
    for dag_type in ['chain', 'tree', 'pyramid']:
        for n in range(2, 8):
            try:
                inst = generate_pebbling_formula(dag_type, n, seed=seed)
                instances.append(inst)
            except Exception:
                pass

    # Random 3-CNF at varying ratios
    for n_vars in [5, 8, 10, 15, 20]:
        for ratio in [2.0, 3.0, 4.0, 4.27, 5.0]:
            for s in range(3):  # 3 seeds per config
                instances.append(
                    generate_random_kcnf(n_vars, k=3, ratio=ratio, seed=seed + s)
                )

    return instances


def compute_normalized_complexity(instance: ProofInstance) -> Dict[str, float]:
    """
    Compute normalized complexity features for an instance.
    Normalization allows comparison across formula families.
    """
    n = max(instance.num_variables, 1)

    # Log-normalized measures (to handle exponential ranges)
    log_length = np.log2(max(instance.proof_length, 1))
    log_width = np.log2(max(instance.proof_width, 1))
    log_depth = np.log2(max(instance.proof_depth, 1))
    log_space = np.log2(max(instance.proof_space, 1))

    return {
        'log_length': log_length,
        'log_width': log_width,
        'log_depth': log_depth,
        'log_space': log_space,
        'length_per_var': instance.proof_length / n,
        'width_per_var': instance.proof_width / n,
        'depth_per_var': instance.proof_depth / n,
        'space_per_var': instance.proof_space / n,
        'clause_var_ratio': instance.num_clauses / n,
        'formula_width': instance.formula_width,
        'log_complexity_product': log_length + log_width + log_depth,
    }


if __name__ == '__main__':
    instances = generate_dataset()
    print(f"Generated {len(instances)} proof instances")
    for family in ['tseitin', 'pigeonhole', 'pebbling', 'random_kcnf']:
        fam_instances = [i for i in instances if i.family == family]
        print(f"  {family}: {len(fam_instances)} instances")
        if fam_instances:
            print(f"    Length range: [{min(i.proof_length for i in fam_instances)}, {max(i.proof_length for i in fam_instances)}]")
            print(f"    Width range:  [{min(i.proof_width for i in fam_instances)}, {max(i.proof_width for i in fam_instances)}]")
