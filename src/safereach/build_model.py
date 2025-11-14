
import json
import math
import numpy as np
from .abstraction import FINISH
from collections import defaultdict
from fractions import Fraction
import pandas as pd 
import os
from typing import List, Any, Dict
from .abstraction import Abstraction
 
# Logs should be in the form of a list of observations, 
# from the observations we can abstract and get state 
# transition
def build_model(logs: List[List[Any]], abs:Abstraction, alpha=1.0):
    state_transitions = [ ]
    state_space = set()
    # Restrict the state space to emprical observed ones.
    for log in logs:
        state_tran = []
        for obs in log: 
            state = abs.encode(obs) 
            state_tran.append(state)
            state_space.add(state) 
        state_transitions.append(state_tran)
    
    K = len(state_space) # extrace
    
    state_idx = abs.get_state_idx(state_space)
    state_interpret = abs.get_state_interpretation(state_space)
    # Initialize count matrix
    transition_counts = np.zeros((K, K), dtype=int)
    for state_tran in state_transitions:
        prev_states = []
        for state in state_tran: 
            if len(prev_states)>0 and prev_states[-1] in state_idx:
                i, j = state_idx[prev_states[-1]], state_idx[state]
                transition_counts[i, j] += 1
            prev_states.append(state)
        print([state_idx[state] for state in prev_states])
    print(transition_counts)

    # For simplicity, we use Laplace smoothing here.
    transition_probs: Dict[int, Dict[int, str]] = {}
    for s_from in list(state_space):
        numerators = []
        denom = 0
        reachable = []
        i = state_idx[s_from]
        for s_to in list(state_space):         
            j = state_idx[s_to]
            count = transition_counts[i, j]
            numerators.append((j, count ))  # Laplace: +1
            denom += count
            reachable.append(j)

        transition_probs[i] = {
            j: f"{n}/{denom}"
            for j, n in numerators if denom !=0 and n != 0
        }
        if len(transition_probs[i].keys()) == 0:
            transition_probs[i][i] = "1.0"
            
    print(transition_probs)
   
    return {
        "states": list(state_space),
        "state_index": state_idx,
        "state_interpret": state_interpret,
        "transition_counts" : {i: {j: int(transition_counts[i, j]) for j in range(K) if transition_counts[i,j] > 0}
          for i in range(K) if any(transition_counts[i, j] > 0 for j in range(K))},
        "transition_probs": transition_probs
    }
  
def store_model(model, dir, abstraction) :
    if not os.path.exists(dir):
        os.mkdir(dir)
    with open(dir + "model.json","w") as f:
        f.write(json.dumps(model))
    with open(dir + "abstraction.json", "w") as f:
        f.write(abstraction.to_json())
        
    export_dtmc_to_prism(model, file_path= dir + "dtmc.prism")
    
def export_dtmc_to_prism(model, file_path="dtmc.prism", initial_state=0):
    states = model['states']
    state_index = model['state_index']
    transitions = model['transition_probs']
    K = len(states)
    with open(file_path, 'w') as f: 

       # Write PRISM DTMC model header
        f.write("dtmc\n\n")
        f.write("module dtmc_model\n\n")
        f.write(f"    s : [0..{K}] init {initial_state};\n\n") # the last node is the state in theory that never be observed in the state, no transition will come in

        # Write transitions for each state
        for state in states:
            i = state_index[state]
            if state not in transitions:
                continue
            row = transitions[state]
            transition_list = []

            for target_state, prob in row.items():
                j = state_index[target_state]
                transition_list.append(f"{prob} : (s'={j})")

            if transition_list:
                f.write(f"    [] s={i} -> {' + '.join(transition_list)};\n")
        f.write(f"    [] s={K} -> 1.0: (s'={K});\n")
        f.write("\nendmodule\n")
