import os
import json
from ..build_model import *
from .abstraction import EmbodiedAbstraction
from .util import *

def embodied_build_model(dir, model_path, alpha=1.0):
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
            log.append(FINISH)
            logs.append(log)

    specs = []
    with open(dir + "/spec") as f:
        specs = json.loads(f.read()) 
    try: 
        # define abstraction level
        abs_predicates = []
        for spec in specs:
            preds = get_predicates_from(spec)
            print(preds[-1])
            abs_predicates = abs_predicates + preds
            # abs_predicates
        # print(specs)
        # print(abs_predicates)
        
        # print("====")
        abstraction = EmbodiedAbstraction(abs_predicates)
        model = build_model(logs, abstraction, alpha)
        if not os.path.exists(model_path):
            os.mkdir(model_path)
        store_model(model, model_path, abstraction)
        
    except Exception as e:

        raise e

LOG_DIR = '/Users/haoyu/SMU/AgentSpec/src/safereach/embodied/merged_sample/'
MODEL_DIR = 'safereach/dtmcs/embodied/'
log_dirs = [f for f in os.listdir(LOG_DIR) if f.startswith('log_raw_t') and not f.endswith("jsonl")]

for dir in log_dirs : 
    model = MODEL_DIR + "merged_" + dir + "/"
    dir = LOG_DIR + dir + "/"
    try: 
        # if not "37" in dir:
        #     continue
        print(dir)
        embodied_build_model(dir, model) 
        # break
    except Exception as e: 
        if str(e).startswith("global"):
            raise e
        print(e)
        # raise e