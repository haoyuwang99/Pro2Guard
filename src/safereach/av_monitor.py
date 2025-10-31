import os
import json 
import pickle
from .autonomous_vehicle.abstraction import AVAbstraction, REACH_PREDICATE, COLLISION_PREDICATE, LAW_VIOLATION_PREDICATE, scenario_law_map
from .runtime_monitor import runtime_monitor
from .autonomous_vehicle.TracePreprocess import raw_to_lawbreaker_API
from .autonomous_vehicle.law import *
 
def load_abstraction(abstraction_desc_path):
    with open(abstraction_desc_path) as f:
        obj = json.load(f)
        rule = obj["rule"]

    return AVAbstraction(rule)


LOG_BASE = "/Users/haoyu/SMU/AgentSpec/src/safereach/autonomous_vehicle/tests/"
DTMC_BASE = "safereach/dtmcs/"

unsafe_predicates = {
    "s1": LAW_VIOLATION_PREDICATE,
    "s2": LAW_VIOLATION_PREDICATE,
    "s3": COLLISION_PREDICATE,
    "s4": LAW_VIOLATION_PREDICATE,
    "s5": LAW_VIOLATION_PREDICATE,
    "s6": LAW_VIOLATION_PREDICATE,
    "s7": LAW_VIOLATION_PREDICATE,
    "s8": COLLISION_PREDICATE,
    "s9": LAW_VIOLATION_PREDICATE,
    "s10": LAW_VIOLATION_PREDICATE,
}
# s6 and s7 violates law at the first timeframe??

# abs = load_abstraction(abs_path)
# unsafe_states = abs.filter()
# unsafe_states = [abs.get_state_idx()[state] for state in list(unsafe_states)]

for scenario in os.listdir(LOG_BASE):

    LOGDIR = f"{LOG_BASE}{scenario}/"
    if scenario in ["s6","s7"]:
        continue
    rule = scenario_law_map[scenario][0]
    abs = AVAbstraction(rule)
    model_path = f"{DTMC_BASE}{scenario}/dtmc.prism"
    cache = {}
    
    predicate = unsafe_predicates[scenario]
    unsafe_states = abs.filter(predicate)
    unsafe_states = [abs.get_state_idx()[state] for state in list(unsafe_states)]
    
    violated_and_detected = 0
    ahead = 0
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
                
        # t_vars = ["t1", "t2"]
        # add tick
        t_event = {} # maps t1 to lexpr
        # for t in t_vars:
        #     lexprs = [lexpr for lexpr, rexpr in abs.implies if t in rexpr.name]
        #     if len(lexprs) != 1:
        #         continue
        #     t_event[t] = lexprs[0]
            
        total_time = traj[-1]["time"]
        violation_time = -1
        violated = False
        monitor_time = -1
        monitored = False
        # calculate violation time:
        # t_values = { var: -1 for var in t_vars}
        for step in traj: 
            # we cannot calculate fit_score at runtime becuase of the overhead.
            # we assume at the current moment, no rule is violated.

            fit_score = float(step["fit_score"][rule])
            step["fit_score"] = {
                rule: 1.0
            }
            if not monitored:
                try :
                    prob = runtime_monitor(step, model_path, abs, set(unsafe_states), cache = cache)
                except:
                    break
                print(prob)
                if not prob < 0.7:
                    monitor_time = step["time"]
                    monitored = True
            if not violated:
                if predicate == COLLISION_PREDICATE and step["collision"] == 1:
                    violation_time = step["time"]
                    violated= True
                elif predicate == LAW_VIOLATION_PREDICATE and fit_score <= 0.0:
                    violation_time = step["time"]
                    violated= True
                    break
                else:
                    pass
        
        if violated:
            if monitor_time == -1:
                print("violated but not detected!")
            else:
                
                violated_and_detected = violated_and_detected + 1
                ahead = ahead + violation_time - monitor_time
        print(f"monitor_time: {monitor_time}")
        print(f"violation_time: {violation_time}")
        # print(f"total_time: {total_time}")
        
    if violated_and_detected==0:
        violated_and_detected = 1
    print(f"{scenario}, {ahead/violated_and_detected}")


# print(unsafe_states)
# # exit(1)
# for f in os.listdir(LOG_DIR):
    # if not f.endswith("pickle"):
    #     continue
    # with open(f"{LOG_DIR}{f}", 'rb') as pic:
    #     trace = pickle.load(pic)["trace"]

    #     time_seq = sorted(list(trace.keys()))
    #     if len(trace.keys()) == 0:
    #         continue
    #     initial_timestamp = time_seq[0]
    #     enforced_trace = []

    #     cache = {}
    #     for i in range(len(time_seq)):
    #         if i%100 == 0:
    #             print(i)
    #         step = trace[time_seq[i]]
    #         observation = raw_to_lawbreaker_API(step, initial_timestamp)
    #         # s_idx = abs.get_state_idx()[abs.encode(observation)]

    #         prob = runtime_monitor(observation, dtmc_path, abs, set(unsafe_states), cache = cache)
    #         # # print(prob)
    #         # if prob < 0.05:
    #         #     print(i)
    #             # print(len(trace))
    #     print(cache)
    #     exit(0)
# with open()