
import subprocess
import re
from .abstraction import Abstraction
from .ctl import *
from .predicate import *

#returns true if intervention needed.  
def runtime_monitor(observation, dtmc_path, abs: Abstraction, state_idx, path_formula: PathFormula, cache={}):  
    # Step 1: Abstraction
    # t = time.time()
    current_state = abs.encode(observation)
    current_state = state_idx[current_state]

    # Step 2: Rewrite DTMC init state
    # t = time.time()
    with open(dtmc_path, 'r') as f:
        model_txt = f.read()

    # this is to cal P(\psi | s_i) where s_i is the current state 
    updated_model = re.sub(
        r's\s*:\s*\[\d+\.\.\d+\]\s+init\s+\d+;',
        lambda m: re.sub(r'init\s+\d+', f'init {current_state}', m.group(0)),
        model_txt
    )

    with open(dtmc_path, 'w') as f:
        f.write(updated_model)
    # Step 4: Run PRISM to check the prob reaching unsafe state
    # First, convert all proposition to state index for DTMC
    

    # formula = "G(a->b)"
    # # convert the formula into PCTL
    
    # # TODO-map from the proposition to state idx.
    # # translate 
    # states = ""
    # if len(unsafe_states)==1:
    #     state = f"s={list(unsafe_states)[0]}"
    # else :
    #     state = "(" +  "|".join([f"s={s}" for s in unsafe_states]) + ")"
    # print(unsafe_states)


    pctl_formula = f"P=? [ G !{state} ]"
    cmd = f"../prism/bin/prism {dtmc_path} -pf \"{pctl_formula}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    match = re.search(r"Result:\s*([0-9.]+)", result.stdout)
    if match:
        prob = float(match.group(1))
        return prob
        # if prob > threshold:
        #     return True
    else:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Could not parse probability from PRISM output.")
    
def to_state(predicate: StatePredicate, abs: Abstraction):
    predicate
    
# prism support  
def path_to_pctl(path: PathFormula):
    if type(path) == Until:
        return f"({to_pctl(path.predicate1)} U {to_pctl(path.predicate1)})"
    elif type(path) == Finally:
        return f"F ({to_pctl(path.predicate)})"
    elif type(path) == Always:
        return f"G ({to_pctl(path.predicate)})"
    elif type(path) == Next:
        return f"X ({to_pctl(path.predicate)})"
    else:
        raise Exception("unsupported exception")
    
def predicate_to_state():
    pass
    
def to_pctl(formula: Any):
    if type(formula)==PathFormula:
        return path_to_pctl(formula)
    elif type(formula) == StatePredicate:
        # we need to know what specific state
        return predicate_to_state()
    