import os
import pickle
import json
from .autonomous_vehicle.monitor import add_timer_preprocess
from .autonomous_vehicle.TracePreprocess import Trace, raw_to_lawbreaker_API
from .build_model import *
from .autonomous_vehicle.abstraction import AVAbstraction, traffic_rules, parse_law, scenario_law_map


def av_build_model(abs, logs, model_path = "default_av.dtmc"): 
    model = build_model(logs, abs)
    store_model(model, model_path, abs)
    
SAMPLES = "/Users/haoyu/SMU/AgentSpec/src/safereach/autonomous_vehicle/samples/"
# SCENEARIO = "safereach/autonomous_vehicle/samples/Law38_1_1/"
for s in os.listdir(SAMPLES):
    SCENEARIO = f"{SAMPLES}{s}/" 
    # if not s in ["s10"]:
    #     continue
    rule_name = scenario_law_map[s][0]
    
    abs = AVAbstraction(rule_name)
    logs = []
    for f in os.listdir(SCENEARIO):
        if not f.endswith("json"):
            continue
        with open(f"{SCENEARIO}{f}" ) as j:
            trace = json.load(j)["trajectory"] 
            preprocessed_trace = add_timer_preprocess(trace, rule_name, ["t1", "t2"])
            logs.append(trace)
    av_build_model(abs, logs, model_path=f"safereach/dtmcs/{s}/")
    

    