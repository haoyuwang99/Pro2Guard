from collections import defaultdict
from typing import Dict, Iterable, List, Tuple, Hashable, Set, Optional
import math

State = Hashable
Trace = Iterable[State]

# transition_counts are {i:{j: count}}
def bound_rhs(i, transition_counts, epsilon, delta):
    
    # number of states |S|
    state_size = len(transition_counts)

    # total visits to state i: n_i = sum_j n_ij
    n_i = sum([transition_counts[i][j] for j in range(state_size)])
    
    delta_prime = delta/state_size
    
    coeff = (2.0 / (epsilon ** 2)) * math.log(2.0 / delta_prime)

    max_H = 0.0
    for n_ij in transition_counts[i]:
        p_ij = n_ij / n_i  # empirical probability n_ij / n_i
        
        inner = abs(0.5 - p_ij) - (2.0 / 3.0) * epsilon
        term = 0.25 - inner**2
        
        # Chen bound: H(n_i, n_ij, ε, δ') = coeff * (1/4 - (|1/2 - p_ij| - 2ε/3)^2)
        # Clamp at 0 to avoid negative values due to numerical issues.
        if term > 0:
            H_ij = coeff * term
        else:
            H_ij = 0.0
        
        if H_ij > max_H:
            max_H = H_ij
    
    return max_H
    
    