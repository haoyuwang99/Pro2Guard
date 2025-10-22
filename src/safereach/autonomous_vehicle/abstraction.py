
import json
import itertools
import math
from deepdiff import DeepDiff
from ..abstraction import Abstraction, FINISH
from .law import *
from typing import Any, Set, List, Dict
import networkx as nx
import matplotlib.pyplot as plt

VARIABLE_APIS = ['gear', 'engineOn', 'direction', 'manualIntervention', \
    'speed', 'acc', 'brake', 'isLaneChanging', 'isOverTaking',\
    'isTurningAround', 'currentLanenumber', 'currentLanedirection', \
    'speedLimitlowerLimit', 'speedLimitupperLimit', 'honkingAllowed',\
    'crosswalkAhead', 'junctionAhead', 'stopSignAhead', 'signalAhead',\
    'stoplineAhead', 'streetLightOn', 'specialLocationAheadlocation', \
    'specialLocationAheadtype', 'trafficLightAheadcolor', 'trafficLightAheadblink', \
    'PriorityNPCAhead', 'PriorityPedsAhead', 'isTrafficJam', 'NPCAheadAhead', 'NPCAheadspeed',\
    'NearestNPCAhead', 'NearestNPCspeed', 'NPCOppositeAhead', 'NPCOppositespeed', 'rain', 'snow',\
    'fog', 'trafficLightAheadArrowDirectioncolor', 'trafficLightAheadArrowDirectionblink', 'visibility']
    
    
REACH_PREDICATE = ("reach_destination", "==", '1')
COLLISION_PREDICATE = ("collision", "==", "1")
LAW_VIOLATION_PREDICATE = ("fit_score", "<=", 0.0)


#predicate is a tuple (lhs, op, rhs)
def eval_pred(observation, predicate):

    lvalue = eval_expr(observation, predicate[0])
    op = predicate[1]
    rvalue = eval_expr(observation, predicate[2])
    return eval_bin_op(lvalue, op, rvalue)

def eval_expr(observation, expr):

    try:
        float(expr)
        return float(expr)
    except ValueError:
        # print(observation.keys())
        return float(observation[expr])

def eval_bin_op(lvalue, op, rvalue):
    if not op in STR_TO_BINOP.keys():
        print("currently unsupported bin op")
    if type(lvalue) != float or type(rvalue) != float:
        raise Exception("Expected lvalue and rvalue to be float")
    binop = STR_TO_BINOP[op]
    return binop(lvalue, rvalue)    

scenario_law_map = {
    "s1": ['rule38_2','rule38_1', 'rule51_4', 'rule51_5'],
    "s2": ['rule51_5','rule44'],
    "s4": ['rule51_5', 'rule44'],
    "s5": ['rule51_5'],
    "s6": ['rule51_4', 'rule38_1'],
    "s7": ['rule51_4', 'rule38_1'], 
    "s9": ['rule53', 'rule44', 'rule51_4', 'rule51_7'],
    # we might want to refine the predicate can be the indicator for collision, and finish journey
    "s3": ['rule38_1', 'rule44', 'rule51_4', 'rule51_7', "collision"],
    "s8": ['rule51_7','rule38_1', 'rule51_4', 'collision'],
    "s10": ['rule51_7'],
}

class AVAbstraction(Abstraction):
    
    # law_str example, see monitor.py:
    # '(  always( (   (   (trafficLightAheadcolor == 3) and \
    #     (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)    ) \
    #     implies (eventually[0,100](speed > 0.5)) ) \
    #   )\
    #  )'
    def __init__(self, rule ):

        if not (rule in traffic_rules):
            raise Exception(f"unsupported rule {rule}")
        self.predicates = parse_law(traffic_rules[rule]).predicates
        self.implies = parse_law(traffic_rules[rule]).implies
        self.rule = rule
        
        self.predicates = sorted(self.predicates)
        
        self.state_space=sorted(list(self.enumerate_possible_states()))
        self.state_idx = None
        self.state_interpretation = None

    # for autonomous vehicle runtime monitoring, we need to add tick variable
    # collision | law violation | reach | predicates 
    def encode(self, observation):
        
        bitstr = ""
        collision = eval_pred(observation, COLLISION_PREDICATE)
        law_violation = observation["fit_score"][self.rule] <= 0.0 
        reach = eval_pred(observation, REACH_PREDICATE)
        
        # if collision/reach/law violation happens, we do not care about predicates.
        if collision :
            return "100" + "0" * (len(self.predicates))
        elif reach:
            return "010" + "0" * (len(self.predicates))
        elif law_violation:
            return "001" + "0" * (len(self.predicates))
        else:
            bitstr = "000"
            
        # if no collision, evaluate the following
        # predicates
        for predicate in self.predicates: 
            pvalue = eval_pred(observation, predicate)
            bitstr = bitstr + "1" if pvalue else bitstr + "0"

        if not bitstr in self.state_space:
            print(bitstr)
            print(self.state_space)
            raise Exception("unvalid state")
            
        return bitstr
    
    
    # collision | law violation | reach | predicates 
    def decode(self, state):
        observation = {}
        observation["collision"] = float(state[0])
        observation["reach_destination"] = float(state[1])
        observation["fit_score"] = {self.rule: "0.0" if state[2] else "1.0"}
        for i in range(3, 3+ len(self.predicates)):
            cur_bit = state[i]
            predicate = self.predicates[i-3]
            var_name = predicate[0]
            op = predicate[1]
            # currently only support float value as rhs
            rvalue = float(predicate[2])
            if op == "==":
                observation[var_name] = rvalue if cur_bit=='1' else rvalue + 1
            elif op == ">=" or op == ">":
                observation[var_name] = rvalue + 1 if cur_bit=='1' else rvalue - 1 
            elif op == '<='or op == "<":
                observation[var_name] = rvalue - 1 if cur_bit=='1' else rvalue + 1
            else: 
                raise Exception(f"unsupported bin op {op}")
        
        return observation

    #assuming that predicates and reach and law violation are not conflict
    def enumerate_possible_states(self) -> Set[str]: 
        
        enums = ['000' + ''.join(bits)  for bits in itertools.product('01', repeat=len(self.predicates))]
        enums.append("100" + "0" * (len(self.predicates)))
        enums.append("010" + "0" * (len(self.predicates)))
        enums.append("001" + "0" * (len(self.predicates)))
        return set(enums)
        # for a in self.predicates:

    # first bit: collision, last bit: reach
    def can_reach(self, state1: str, state2: str) -> bool:
        # crash as absorbing state. 
        # After crash, although the vehicle in simulator still run after crash,
        # it is unreal and should be consider as the end of the episode.
        if state1.startswith("1"):
            return False
        # if the vehicle succesfully arrive, the episode ends.
        if state1.startswith("01"):
            return False
        return True

    # specs is a list of predicates and its coressponding boolean value. 
    # each spec in specs is a condition on the observation.
    # currently, we support collision, reach and law violation.
    def filter(self, spec = (COLLISION_PREDICATE,True)) -> Set[str]:
        supported_specs = [COLLISION_PREDICATE, REACH_PREDICATE, LAW_VIOLATION_PREDICATE]

        if not spec in supported_specs :
            raise Exception("unsupported predicate")
        
        res = set()

        if spec == COLLISION_PREDICATE:
            res.add("100" + "0" * len(self.predicates))
        elif spec == REACH_PREDICATE:
            res.add("010" + "0" * len(self.predicates))
        elif spec == LAW_VIOLATION_PREDICATE:
            res.add("001" + "0" * len(self.predicates))
        else:
            raise Exception(f"Unexpected Spec: {spec}")
        return res   

    def get_state_idx(self) -> Dict[str, int]:  
        if self.state_idx == None:
            self.state_idx = {s:i for i, s in enumerate(self.state_space)}
        return self.state_idx

    def get_state_interpretation(self) -> Dict[str, Any]:
        if self.state_interpretation == None:
            self.state_interpretation = {s: list(zip([f"{p[0]} {p[1]} {p[2]}" for p in self.predicates],\
                [ True if bit == '1' else False for bit in s])) for s in self.state_space}

        return self.state_interpretation
    
    def to_json(self) -> str:
        obj = {
            "predicates":  self.predicates,
            "reach" : REACH_PREDICATE, 
            "collision": COLLISION_PREDICATE,
            "rule":self.rule
        }
        return json.dumps(obj)
    
