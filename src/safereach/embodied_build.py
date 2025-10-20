import os
import json
from .build_model import *
from .embodied.abstraction import EmbodiedAbstraction

def embodied_build_model(dir, model_path, alpha=1.0): 
    print(dir)
    print(model_path)
    
    if not os.path.exists( dir + "/spec"):
        # os.system(f"mv {dir} samples/embodied_no_final_state")
        return
    logs = []
    for f in os.listdir(dir):
        if not f.endswith("json"):
            continue
        with open( dir + "/" + f) as f:
            obj = json.loads(f.read())
            log = [o["state"] for o in obj["s_trans"]]
            logs.append(log)

    
    specs = []
    with open(dir + "/spec") as f:
        specs = json.loads(f.read()) 
    print(specs)
    try: 
        # define abstraction level
        object_types = set()
        keys = set()
        recepatacles = set()
        for spec in specs:
            object_types.add(spec.get("objectType", ""))
            for key in spec:
                keys.add(key)
            for recep in spec.get("parentReceptacles", []):
                recepatacles.add(recep)
                
        keys.remove("objectType")
        if "parentReceptacles" in keys:
            keys.remove("parentReceptacles")
            
        abstraction = EmbodiedAbstraction(object_types, keys, recepatacles)
        model = build_model(logs, abstraction, alpha)
        model_path = f"{model_path}{alpha}/"
        if not os.path.exists(model_path):
            os.mkdir(model_path)
        print(model_path)
        # print(model)
        store_model(model, model_path, abstraction)
    except Exception as e:
        raise e

LOG_DIR = 'safereach/embodied/merged_sample/'
MODEL_DIR = 'safereach/embodied/dtmcs/'
log_dirs = [f for f in os.listdir(LOG_DIR) if f.startswith('log_raw_t') and not f.endswith("jsonl")]
for dir in log_dirs : 
    model = MODEL_DIR + "merged_" + dir + "/"
    dir = LOG_DIR + dir + "/"
    try: 
        embodied_build_model(dir, model) 
        # break
    except Exception as e:
        # raise e
        # continue
        print(e) 