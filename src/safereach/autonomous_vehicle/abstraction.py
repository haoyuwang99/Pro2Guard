
import json
import itertools
import math
from deepdiff import DeepDiff
from ..abstraction import Abstraction, FINISH
from .law import *
from typing import Any, Set, List, Dict, Mapping
import networkx as nx
import matplotlib.pyplot as plt
from z3 import Bool, FP, FPVal, Float32, And, Or, Not, Solver, sat
from ..predicate import *

OP_MAP = {
    'and': And,
    'or': Or,
    'not': Not,
    '==': lambda a, b: a == b,
    '!=': lambda a, b: a != b,
    '>':  lambda a, b: a > b,
    '<':  lambda a, b: a < b,
    '>=': lambda a, b: a >= b,
    '<=': lambda a, b: a <= b,
    '=>': Implies
}

OP_STR_MAP = { 
    '==': "eq",
    '!=': "neq",
    '>': "gt",
    '<': "lt",
    '>=': "geq",
    '<=': "leq"
}

NEGATE_OP = {
    '==': '!=',
    '!=': '==',
    '>':  '<=',
    '<':  '>=',
    '>=': '<',
    '<=': '>',
}

def is_valid_state(bitstr, predicates):
    if len(bitstr) != len(predicates):
        raise Exception("")
    s = Solver()
    for predicate, value in zip(predicates, bitstr): 
        var = FP(predicate[0], Float32()) 
        op = predicate[1]
        val = predicate[2]
        if value == '0':
            s.add(OP_MAP[NEGATE_OP[op]](var, FPVal(float(val), Float32())) )
        else:
            s.add(OP_MAP[op](var, FPVal(float(val), Float32())))
    return s.check() == sat
        

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
    
    
REACH = AtomicPredicate(lhs="reach_destination", op="==", rhs=1)
COLLISION = AtomicPredicate(lhs="collision", op="==", rhs=1)

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

def convert_to_bool_var(lhs, op, rhs): 
    return f"{lhs}_{op}_{rhs}"

scenario_law_map = {
    "s1": ['rule38_2','rule38_1', 'rule51_4', 'rule51_5'],
    "s2": ['rule51_5','rule44'],
    "s4": ['rule51_5', 'rule44'],
    "s5": ['rule51_5'],
    "s6": ['rule51_4', 'rule38_1'],
    "s7": ['rule51_4', 'rule38_1'], 
    "s9": ['rule53', 'rule44', 'rule51_4', 'rule51_7'],
    "s3": ['rule38_1', 'rule44', 'rule51_4', 'rule51_7', "collision"],
    "s8": ['rule51_7','rule38_1', 'rule51_4', 'collision'],
    "s10": ['rule51_7'],
}

def satisfy(observation, formula) -> bool:
    # formula -> predicates
    # evalulate propositions
    # eval formula
    pass

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
        collector = parse_law(traffic_rules[rule])
        self.predicates = collector.predicates
        self.implies = collector.implies
        self.rule = rule

        self.predicates = sorted(list(set(self.predicates)))
        # We asumme the rhs of the AV predicate is always float
        self.predicates = [AtomicPredicate(lhs=p[0], op=p[1], rhs=float(p[2]) ) for p in self.predicates]
        
    # for autonomous vehicle runtime monitoring, we need to add tick variable
    # collision | reach | predicates 
    def encode(self, observation):
        bitstr = ""
        collision = COLLISION.state_eval(observation) 
        reach = REACH.state_eval(observation)
        
        # if collision/reach/law violation happens, we do not care about predicates.
        if collision :
            return "10" + "0" * (len(self.predicates))
        elif reach:
            return "01" + "0" * (len(self.predicates))
        else:
            bitstr = "00"
            
        # if no collision, evaluate the following
        # predicates
        for predicate in self.predicates: 
            print(predicate)
            pvalue = predicate.state_eval(observation)
            bitstr = bitstr + "1" if pvalue else bitstr + "0"
            
        return bitstr
    
    # collision | reach | predicates 
    def decode(self, state):
        observation = {}
        observation["collision"] = float(state[0])
        observation["reach_destination"] = float(state[1])
        # observation["fit_score"] = {self.rule: "0.0" if state[2] else "1.0"}
        EXTRA = 2
        for i in range(EXTRA, EXTRA + len(self.predicates)):
            cur_bit = state[i]
            predicate = self.predicates[i - EXTRA]
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

    def enumerate_possible_states(self) -> Set[str]: 
        s_space = [ bitstr for bitstr in itertools.product('01', repeat=len(self.predicates)) \
            if is_valid_state(bitstr, self.predicates)]
        enums = ['00' + ''.join(bits)  for bits in s_space]
        enums.append("10" + "0" * (len(self.predicates)))
        enums.append("01" + "0" * (len(self.predicates))) 
        return set(enums)

    # first bit: collision, last bit: reach
    def valid_trans(self, state1: str, state2: str) -> bool:
        # crash as absorbing state. 
        # After crash, although the vehicle in simulator still run after crash,
        # it is unreal and should be consider as the end of the episode.
        if state1.startswith("1"):
            return False
        # if the vehicle succesfully arrive, the episode ends.
        if state1.startswith("01"):
            return False
        return True

    def get_state_idx(self, states) -> Mapping[str, int]:  
        self.state_idx = {s:i for i, s in enumerate(states)}
        return self.state_idx

    def filter(self, spec = (COLLISION,True)) -> List[str]:
        
        supported_specs = [COLLISION, REACH]

        # if not spec in supported_specs :
        #     raise Exception("unsupported predicate")
        res= []
        for s in self.state_space:
            observation = self.decode(s)
            if satisfy(observation, spec):
                res.append(s)
            
        # if spec == COLLISION:
        #     res.add("10" + "0" * len(self.predicates))
        # elif spec == REACH:
        #     res.add("01" + "0" * len(self.predicates))
        # else:
        #     raise Exception(f"Unexpected Spec: {spec}")
        return [self.state_idx[s] for s in res]   
    
    def get_state_interpretation(self, states) -> Mapping[str, Mapping[str, bool]]: #Mapping: predicate str -> value

        predicates = [convert_to_bool_var(p.lhs, p.op, p.rhs) for p in [COLLISION, REACH] + self.predicates]

        state_interpretation = {}

        for s in states:
            bool_vals = [ True if bit == '1' else False for bit in s]
            s_interp = {}
            for pred, val in zip(predicates, bool_vals):
                # print(self.sta)
                s_interp[pred] = val
            state_interpretation[s] = s_interp    
            
        return state_interpretation
    
    def to_json(self) -> str:
        obj = {
            "predicates":  [p.model_dump_json() for p in self.predicates],
            "rule":self.rule
        }
        return json.dumps(obj)
    
