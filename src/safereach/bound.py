from collections import defaultdict
from typing import Dict, Iterable, List, Tuple, Hashable, Set, Optional

State = Hashable
Trace = Iterable[State]

def learn_dtmc_with_laplace(
    traces: List[List[State]],
    alpha: float = 1.0,
    valid_out: Optional[Dict[State, Set[State]]] = None,
):
    """
    Learn DTMC transitions with Laplace smoothing.

    Returns:
        states: sorted list of states
        counts: dict[(i,j)] -> n_ij
        row_counts: dict[i] -> n_i (sum_j n_ij)
        mle_P: dict[i] -> dict[j] -> p_ij (unsmoothed MLE; rows with n_i==0 are empty)
        smooth_P: dict[i] -> dict[j] -> p_ij (Laplace smoothed over valid successors)
        k_out: dict[i] -> k_i (number of valid outgoing transitions used for smoothing)
    """
    # Collect states and transition counts
    counts = defaultdict(int)     # n_ij
    row_counts = defaultdict(int) # n_i
    states_set = set()

    for tr in traces:
        if not tr:
            continue
        states_set.update(tr)
        for u, v in zip(tr, tr[1:]):
            counts[(u, v)] += 1
            row_counts[u] += 1
            states_set.add(u); states_set.add(v)

    states = sorted(states_set, key=lambda x: str(x))

    # Build observed successors per state (for default k_i)
    observed_succ = defaultdict(set)
    for (u, v), c in counts.items():
        if c > 0:
            observed_succ[u].add(v)

    # Decide valid successors for smoothing
    # If valid_out is given, use it; else use observed successors (standard and safer by default).
    succ = {}
    for s in states:
        if valid_out is not None and s in valid_out and len(valid_out[s]) > 0:
            succ[s] = set(valid_out[s])
        else:
            succ[s] = set(observed_succ[s])  # may be empty if no outgoing observed

    # Build MLE and smoothed distributions
    mle_P: Dict[State, Dict[State, float]] = {s: {} for s in states}
    smooth_P: Dict[State, Dict[State, float]] = {s: {} for s in states}
    k_out: Dict[State, int] = {}

    for i in states:
        k_i = len(succ[i])
        k_out[i] = k_i
        n_i = row_counts[i]

        # MLE (only supported where n_i > 0); zero-row stays empty
        if n_i > 0:
            for j in succ[i] if k_i > 0 else []:
                n_ij = counts[(i, j)]
                mle_P[i][j] = n_ij / n_i

        # Laplace smoothing over the chosen valid successors
        if k_i > 0:
            denom = n_i + alpha * k_i
            for j in succ[i]:
                n_ij = counts[(i, j)]
                smooth_P[i][j] = (n_ij + alpha) / denom
        else:
            # No valid successors: leave empty (degenerate/absorbing row with no observed/allowed outs)
            smooth_P[i] = {}

    return states, counts, row_counts, mle_P, smooth_P, k_out


def total_variation_and_l1_between_rows(
    p: Dict[State, float],
    q: Dict[State, float],
    support: Set[State],
) -> Tuple[float, float]:
    """
    Compute TV and L1 distances between two discrete distributions over a common support.
    Missing keys are treated as 0.

    TV = 0.5 * L1.
    """
    l1 = 0.0
    for s in support:
        l1 += abs(p.get(s, 0.0) - q.get(s, 0.0))
    return 0.5 * l1, l1


def bound(
    traces: List[List[State]],
    alpha: float = 1.0,
    valid_out: Optional[Dict[State, Set[State]]] = None,
):
    """
    Main entry:
      1) Learn DTMC with Laplace smoothing (α).
      2) Compute B(A_W) as the max per-row total-variation distance
         between smoothed and unsmoothed (MLE) transition rows.

    Returns a dict with:
        - states, counts, row_counts, k_out
        - mle_P, smooth_P
        - B_per_state_TV: dict[state] -> TV distance
        - B_per_state_L1: dict[state] -> L1 distance
        - B_max_TV  : max TV over states (our B(A_W) by default)
        - B_max_L1  : max L1 over states
    """
    (states, counts, row_counts, mle_P, smooth_P, k_out) = learn_dtmc_with_laplace(
        traces=traces, alpha=alpha, valid_out=valid_out
    )

    B_per_state_TV = {}
    B_per_state_L1 = {}

    for i in states:
        # Use the union of supports used for each row’s comparison
        support = set(smooth_P[i].keys()) | set(mle_P[i].keys())
        if len(support) == 0:
            # No outgoing distribution either way → distance 0
            tv = 0.0
            l1 = 0.0
        else:
            tv, l1 = total_variation_and_l1_between_rows(mle_P[i], smooth_P[i], support)
        B_per_state_TV[i] = tv
        B_per_state_L1[i] = l1

    B_max_TV = max(B_per_state_TV.values(), default=0.0)
    B_max_L1 = max(B_per_state_L1.values(), default=0.0)

    return {
        "states": states,
        "counts": counts,
        "row_counts": row_counts,
        "k_out": k_out,
        "mle_P": mle_P,
        "smooth_P": smooth_P,
        "B_per_state_TV": B_per_state_TV,
        "B_per_state_L1": B_per_state_L1,
        "B_max_TV": B_max_TV,   # use this as B(A_W) by default
        "B_max_L1": B_max_L1,
        "alpha": alpha,
    }
