import os
import json 
import time
import pickle
from .abstraction import convert_to_bool_var,AVAbstraction, REACH, COLLISION, scenario_law_map
from ..runtime_monitor import *
from .TracePreprocess import raw_to_lawbreaker_API
from .law import *
from ..predicate import *
 
FIT_THRESHOLD = 1.2
 
THRESHOLD = 0.7
def load_abstraction(abstraction_desc_path):
    with open(abstraction_desc_path) as f:
        obj = json.load(f)
        rule = obj["rule"]
    return AVAbstraction(rule)

BOUNDED_RESPONSE = "bound"
LAW_VIOLATION_PREDICATE = "law"
LOG_BASE = "/Users/haoyu/SMU/AgentSpec/src/safereach/autonomous_vehicle/tests/"
DTMC_BASE = "safereach/dtmcs/"

unsafe_predicates = {
    "s1": LAW_VIOLATION_PREDICATE,
    "s2": LAW_VIOLATION_PREDICATE,
    "s3": COLLISION,
    "s4": LAW_VIOLATION_PREDICATE,
    "s5": LAW_VIOLATION_PREDICATE,
    "s6": LAW_VIOLATION_PREDICATE,
    "s7": LAW_VIOLATION_PREDICATE,
    "s8": COLLISION,
    "s9": LAW_VIOLATION_PREDICATE,
    "s10": LAW_VIOLATION_PREDICATE,
}

# s6 and s7 violates law at the first timeframe??

# abs = load_abstraction(abs_path)
# unsafe_states = abs.filter()
# unsafe_states = [abs.get_state_idx()[state] for state in list(unsafe_states)]

#interp: propositions in the form of {(lhs, op, rhs): bool_val ...}
# it returns the value of the predicate.

def monitor_automata(alpha, beta, armed, t, viol, K):
    if not viol and alpha:
        t = K
        armed = True
    elif not viol and armed and beta:
        t = 0
        armed = False
    elif not viol and armed and not alpha and not beta and t>1:
        t = t-1
    elif not viol and armed and not alpha and not beta and t==1:
        viol = True
    return armed, t, viol
    

for scenario in os.listdir(LOG_BASE):
    LOGDIR = f"{LOG_BASE}{scenario}/"
    if scenario in ["s3","s6","s7", ".DS_Store"]:
        continue
    
    rule = scenario_law_map[scenario][0]
    abs = AVAbstraction(rule)
    model_path = f"{DTMC_BASE}{scenario}/dtmc.prism"
    model_des = f"{DTMC_BASE}{scenario}/model.json"
    with open(model_des) as f:
        obj = json.loads(f.read())
        state_idx = obj["state_index"]
        state_interp = obj["state_interpret"]
        unobserved_state = len(state_idx.keys())
        
    cache = {}
    
    violated_and_detected = 0
    ahead = 0
    predicate = unsafe_predicates[scenario]
    if predicate == COLLISION: 
        # continue
        unsafe_states = filter(state_interp, COLLISION )
        unsafe_states = [state_idx[state] for state in list(unsafe_states)]
        
        overhead = 0
        num = 0
        for log in os.listdir(LOGDIR):
            if log.find("00000") == -1:
                continue
            if not log.endswith("_c.json"):
                continue 
            
            
            traj = []
            with open(f"{LOGDIR}{log}") as f:
                traj = json.load(f)["trajectory"]
            nexts = [ o for o in os.listdir(LOGDIR)\
                if o.startswith(log[:log.find(".")]) and o.find("00000")==-1 and o.endswith("json")]
            for n in nexts:
                with open(f"{LOGDIR}{n}") as f:
                    traj.extend(json.load(f)["trajectory"]) 
            t_event = {} # maps t1 to lexpr
                
            total_time = traj[-1]["time"]
            violation_time = -1
            violated = False
            monitor_time = -1
            monitored = False
            for step in traj: 
                if step["mindisttoego"] <= FIT_THRESHOLD and not monitored:
                    monitored = True
                    monitor_time = step["time"]
                
                if step["mindisttoego"] <=0:
                    violated = True
                    violation_time = step["time"]
                    break
                    
                continue
                # if step["min_dist_to_ego"]
                if not monitored:
                    try :
                        # translate the STL formula to PCTL (which depends on runtime information)
                       
                        prob = state_runtime_monitor(step, model_path, abs, state_idx, unsafe_states, cache = cache)
                      
                    except Exception as e:
                        raise e
                    if prob < THRESHOLD:
                        monitor_time = step["time"]
                        monitored = True
                if not violated and step["collision"] == 1:
                    print("Collision detected!!!")
                    violation_time = step["time"]
                    violated= True
            
            if violated:
                if monitor_time == -1:
                    print("violated but not detected!")
                else:
                    violated_and_detected = violated_and_detected + 1
                    ahead = ahead + violation_time - monitor_time
                
                print(f"monitor_time: {monitor_time}")
                print(f"violation_time: {violation_time}")
        # print(f"average overhead: {overhead/num}")
    else : #LAW VIOLATION
        continue
        # 1. parse varphi_s, varphi_t and K from the rule
        components = [] #(predicate s, predicate t, K)

        for imply in abs.implies:
            pre = convert(imply[0])
            post, K = parse_K_eventually(imply[1])
            post = convert(post)
            pre_states = filter(state_interp, pre)
            pre_states = [state_idx[state] for state in pre_states] if len(pre_states) > 0 else [len(state_idx.keys())] #fallback state

            post_states = filter(state_interp, post)
            post_states = [state_idx[state] for state in post_states]if len(pre_states) > 0 else [len(state_idx.keys())] #fallback state

            components.append((pre_states, post_states, int(K)))
        # print(rule)
        # print(components)
        
        sync_dtmc_path = construct_br_monitor(model_path, abs.rule, pre_states, post_states, K)
        
        overhead = 0
        num = 0
        for log in os.listdir(LOGDIR):
            if log.find("00000") == -1:
                continue
            if not log.endswith(".json"):
                continue 
            
            traj = []
            with open(f"{LOGDIR}{log}") as f:
                traj = json.load(f)["trajectory"]
            nexts = [ o for o in os.listdir(LOGDIR)\
                if o.startswith(log[:log.find(".")]) and o.find("00000")==-1 and o.endswith("json")]
            for n in nexts:
                with open(f"{LOGDIR}{n}") as f:
                    traj.extend(json.load(f)["trajectory"]) 
            t_event = {} # maps t1 to lexpr
                
            total_time = traj[-1]["time"]
            violation_time = -1
            violated = False
            monitor_time = -1
            monitored = False
            
            t = 0
            armed = False
            viol = False
            for step in traj: 
                fit_score = float(step["fit_score"][rule])
                if not monitored and fit_score <= FIT_THRESHOLD:
                    monitored = True
                    monitor_time = step["time"]

                if not violated and fit_score <= 0.0:
                    violation_time = step["time"]
                    violated= True
                    break 
                continue
                current_state = abs.encode(step)
                current_state = state_idx[current_state] if current_state in state_idx else len(state_idx.keys())
                alpha = current_state in pre_states
                beta = current_state in post_states

                armed, t, viol = monitor_automata(alpha, beta, armed, t, viol, K)
                if not monitored:
                    try :
                        overhead = overhead + time.time()
                        # translate the STL formula to PCTL (which depends on runtime information)
                        prob = runtime_br_monitor(sync_dtmc_path, current_state, armed, t, viol, cache = cache)
                          
                        overhead = overhead - time.time()
                        num = num +1# print(prob)
                    except Exception as e:
                        raise e
                    if prob < THRESHOLD:
                        monitor_time = step["time"]
                        monitored = True
                        
                if not violated and fit_score <= 0.0:
                    violation_time = step["time"]
                    violated= True
                    break
                
            if violated:
                if monitor_time == -1:
                    print("violated but not detected!")
                else:
                    violated_and_detected = violated_and_detected + 1
                    ahead = ahead + violation_time - monitor_time
                
                print(f"monitor_time: {monitor_time}")
                print(f"violation_time: {violation_time}")
                
        if num ==0:
            continue
        print(f"average overhead: {overhead/num}")
        # print(f"total_time: {total_time}")        
    if violated_and_detected==0:
        violated_and_detected = 1
        
    print(f"{rule},{scenario}, {ahead/violated_and_detected}")
