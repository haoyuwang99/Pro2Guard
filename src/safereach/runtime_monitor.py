
import subprocess
import re, os
from .abstraction import Abstraction
from .ctl import *
# from .predicate import *
from typing import List

#returns true if intervention needed.  
def state_runtime_monitor(observation, dtmc_path, abs: Abstraction, state_idx, unsafe_states: List[int], cache={}):  
    # Step 1: Abstraction
    # t = time.time()
    current_state = abs.encode(observation)
    print(current_state)
    current_state = state_idx[current_state] if current_state in state_idx else len(state_idx.keys())
    if current_state == len(state_idx.keys()):
        print("what?")

    to = "|".join([str(s) for s in unsafe_states])
    key = f"from: {current_state} to {to}"
    if key in cache:
        return cache[key]
    
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
    
    state = "|".join(["s=" + str(s) for s in unsafe_states])
    pctl_formula = f"P=? [ G !({state}) ]"
    # print(pctl_formula)
    cmd = f"../prism/bin/prism {dtmc_path} -pf \"{pctl_formula}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    match = re.search(r"Result:\s*([0-9.]+)", result.stdout)
    if match:
        prob = float(match.group(1))
        cache[key] = prob
        return prob
        # if prob > threshold:
        #     return True
    else:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Could not parse probability from PRISM output.")
    
MONITOR_TEMPLATE = """

{DTMC}
 
//α -> F[0,K] β 
const int K = {K};
formula alpha = {pre_states}; // α holds 
formula beta  = {res_states}; // β holds 

module mon_R1

    armed : bool init false; // whether β is expected soon
    t     : [0..K] init 0;   // remaining steps
    viol  : bool init false; // violation flag (absorbing)

    // α holds → (re)start the countdown
    [tick] !viol & alpha -> (armed'=true) & (t'=K);

    // β satisfies the obligation
    [tick] !viol & armed & beta -> (armed'=false) & (t'=0);

    // Waiting: decrement the countdown
    [tick] !viol & armed & !beta & !alpha & (t>1) -> (t'=t-1);

    // Deadline passed → violation
    [tick] !viol & armed & !beta & !alpha & (t=1) -> (viol'=true);

    // Absorb when violated
    [tick] viol -> (viol'=true);

endmodule

"""

def construct_br_monitor(dtmc_path, rule, pre_states, post_states, K ):

    sync_dtmc_path = dtmc_path[:-6] + f"_{rule}.prism" 
    
    if not os.path.exists(sync_dtmc_path):
        with open(dtmc_path) as f:
            dtmc = f.read()
            
        pre_states = "(" + "|".join(["s=" + str(s) for s in pre_states])+ ")"
        post_states = "(" + "|".join(["s=" + str(s) for s in post_states])+ ")"
        
        # print(sync_dtmc_path)
        sync_dtmc = MONITOR_TEMPLATE.format(DTMC=dtmc,pre_states=pre_states, res_states = post_states, K=K)
        with open(sync_dtmc_path, "w") as f:
            f.write(sync_dtmc)
    
    return sync_dtmc_path
        
# the cache should be invalidated after changing the rule/scenario
def runtime_br_monitor( dtmc_path, current_state, armed, t, viol, cache = {}):
    # 1. get the current state s, armed, t, viol from previous trace
    
    key = f"{current_state}_{armed}_{t}_{viol}"
    if key in cache:
        return cache[key]
    
    # TODO-set the current state (s, armed, t, viol) for the synchronised DTMC.
    with open(dtmc_path) as f:
        model_txt = f.read()
    
    
    model_txt = re.sub(
        r's\s*:\s*\[\d+\.\.\d+\]\s+init\s+\d+;',
        lambda m: re.sub(r'init\s+\d+', f'init {current_state}', m.group(0)),
        model_txt
    )
    
    model_txt = re.sub(
        r'armed\s*:\s*bool\s*init\s*(true|false)\s*;',
        f'armed : bool init {str(armed).lower()};',
        model_txt
    )
    
    model_txt = re.sub(
        r't\s*:\s*\[0\.\.K\]\s*init\s*\d+\s*;',
        f't : [0..K] init {t};',
        model_txt
    )

    # viol init replacement
    model_txt = re.sub(
        r'viol\s*:\s*bool\s*init\s*(true|false)\s*;',
        f'viol : bool init {str(viol).lower()};',
        model_txt
    )


    with open(dtmc_path, 'w') as f:
        f.write(model_txt)
        
    pctl_formula = "P=?[G !viol]"
    
    cmd = f"../prism/bin/prism {dtmc_path} -pf \"{pctl_formula}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    match = re.search(r"Result:\s*([0-9.]+)", result.stdout)
    if match:
        prob = float(match.group(1))
        cache[key] = prob
        return prob
        # if prob > threshold:
        #     return True
    else:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Could not parse probability from PRISM output.")
