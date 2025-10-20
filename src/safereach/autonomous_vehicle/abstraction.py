
import json
import itertools
import operator
import math
from deepdiff import DeepDiff
from ..abstraction import Abstraction, FINISH
from typing import Any, Set, List, Dict
import networkx as nx
import matplotlib.pyplot as plt
import rtamt

from rtamt.syntax.node.ltl.predicate import Predicate
from rtamt.syntax.node.ltl.implies import Implies
# from rtamt.syntax.node.ltl.binary_node import BinaryNode
from rtamt.syntax.ast.visitor.stl.ast_visitor import StlAstVisitor

def prepare_for_rule38_1():              
    #GREEN = 3; 
    # Note: the conversion from eventually[0,100](speed > 0.5) to eventually(time <= 100 and speed > 0.5)
    # introduces a new variable time, which requires a counter from left event 
    # (i.e., (trafficLightAheadcolor == 3) and  (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0) ) being triggered.
    
    # 1: add tick, add 1 if precondition not satisfied, reset to 0 if event triggered.
    # 2:  eventually p = for any time point later, exist p is satisfied
    traffic_rule = '(\
                            always( (   (   (trafficLightAheadcolor == 3) and \
                                            (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)    ) \
                                implies (eventually((t1 <= 100) and (speed > 0.5))) ) \
                            )\
                    )'
    return traffic_rule

# t1 and t2 indicate the time after satifaction of first and second precondition
def prepare_for_rule38_2():              
    #YELLOW = 2;
    traffic_rule = '(\
                            always(\
                                    ( \
                                        (\
                                            (trafficLightAheadcolor == 2) and ((currentLanenumber == 0))\
                                        ) implies ( eventually((t1 <= 100) and (speed > 0.5)) )\
                                    ) and \
                                    ( \
                                        (\
                                            (trafficLightAheadcolor == 2) and ((currentLanenumber > 0))\
                                        ) implies ( eventually((t2 <= 100) and (speed < 0.5)) )\
                                    ) \
                            ) \
                        )'
    return traffic_rule

def prepare_for_rule38_3():              
    #RED = 1;   
    traffic_rule = '(\
                            always((((trafficLightAheadcolor == 1) and \
                                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and\
                                (currentLanenumber > 0) and \
                                (direction <= 1)) \
                                implies ( eventually((t1<= 100) and (speed < 0.5)) )) and \
                                (((trafficLightAheadcolor == 1) and \
                                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
                                (direction == 2) and (PriorityNPCAhead == 0) and \
                                (currentLanenumber > 0) and \
                                (PriorityPedsAhead == 0) ) \
                                implies ( eventually((t2 <= 100) and (speed > 0.5)) )) ) \
                            )'
    return traffic_rule

# def prepare_for_rule38():              
#     # message TrafficLight {
#     #   enum Color {
#     #     UNKNOWN = 0;
#     #     RED = 1;
#     #     YELLOW = 2;
#     #     GREEN = 3;
#     #     BLACK = 4;
#     #   };       
#     # we should put different weight on different variables!
#     traffic_rule = '(always(((trafficLightAheadcolor == 3) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)) implies ( speed >= 0.1 ))   and \
#                             always((((trafficLightAheadcolor == 2) and ((stoplineAhead == 0) or (stoplineAhead > 50))) implies ( speed > 0.1 )) and \
#                                     (((trafficLightAheadcolor == 2) and (stoplineAhead <= 2)) implies (speed < 0.1)) ) and \
#                             always((((trafficLightAheadcolor == 1) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (direction <= 1)) implies ( speed < 0.1 )) and \
#                                     (((trafficLightAheadcolor == 1) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (direction == 2) and (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0) ) implies ( speed >= 0.1 )) ) \
#                             )'
#     return traffic_rule

def prepare_for_rule42():
    # \begin{aligned}
    #     & G(((trafficLightAhead.color = yellow \land \\
    #     & trafficLightAhead.blink) \lor \\
    #     & (trafficLightAhead.direction.color = yellow \land \\
    #     & trafficLightAhead.direction.blink)) \land \\
    #     & ( stoplineAhead(realvalue) \lor junctionAhead(realvalue) )\\
    #     & \implies speed < realvalue )
    # \end{aligned}          
    traffic_rule = '(always(((trafficLightAheadcolor == 2) and \
                            (trafficLightAheadblink == 1) and \
                            ((stoplineAhead <= 1) or (junctionAhead <= 1)))\
                            implies (speed < 5))\
                            )'
    return traffic_rule

def prepare_for_rule44():
    # \begin{aligned}
    #     & G(currentLane.number \geq 2  \implies \\
    #     & (speed \geq speedLimit.lowerLimit \land  \\
    #     & speed \leq speedLimit.upperLimit)) \land \\
    #     & G(isLaneChanging \land   currentLane.number \geq 2 \\
    #     & \implies  \lnot PriorityNPCAhead)
    # \end{aligned}          
    traffic_rule = '(   always( (currentLanenumber >= 201) \
                                implies ((eventually[0,6000](currentLanenumber >= 201 implies speed >= 20)) and (speed <= speedLimitupperLimit))))'
    return traffic_rule

def prepare_for_rule45():
    # \begin{aligned}
    #     & G(speed \geq speedLimit.lowerLimit  \land \\
    #     & speed \leq speedLimit.upperLimit )
    # \end{aligned}    
    traffic_rule = '(always((speed >= speedLimitlowerLimit) and (speed <= speedLimitupperLimit)))'
    return traffic_rule

def prepare_for_rule46_2():
    # \begin{aligned}
    #     & G( (direction \neq forward) \lor isTurningAround) \\
    #     & \implies   speed \leq 30 )
    # \end{aligned}
    traffic_rule = '(always(((direction == 1) or (direction == 2) or (isTurningAround == 1))\
                            implies (speed <= 30)))'
    return traffic_rule

def prepare_for_rule46_3():
    # \begin{aligned}
    #     & G((Weather.rain \geq 0.5 \lor Weather.fog \geq 0.5 \\
    #     & \lor  Weather.snow \geq 0.5) \land Weather.visibility \leq 50 \\
    #     & \implies speed \leq 30)
    # \end{aligned}
    traffic_rule = '(always(((rain >= 0.5) or (fog >= 0.5) or (snow >= 0.5))\
                            implies (speed <= 30)))'

    return traffic_rule

def prepare_for_rule47():
    # $$
    # \begin{aligned}
        # & G(isOverTaking \implies  turnSignal = left \land \\
        # & (F[-realvalue,\ realvalue](hornOn) \lor \\
        # & ( highBeamOn \land (highBeamOn \\
        # & \implies   F[0,\ realvalue](lowBeamOn) )) \lor \\
        # & ( lowBeamOn \land (lowBeamOn \\
        # & \implies   F[0,\ realvalue](highBeamOn) )))  \land  \\
        # & F[0,\ realvalue]( (turnSignal = right \land \\
        # & isLaneChanging \implies NearestNPC(realvalue) \\
        # & \land isLaneChanging) )
    # \end{aligned}
    # $$
    traffic_rule = '(always((isOverTaking == 1)\
                            implies ( (turnSignal == 1) and \
                                ((eventually[-1, 2](hornOn == 1)) or \
                                    ( \
                                    ((highBeamOn == 1 ) and \
                                        ((highBeamOn == 1) implies (eventually[0, 2](lowBeamOn == 1))) ) or \
                                    ((lowBeamOn == 1 ) and \
                                        ((lowBeamOn == 1) implies (eventually[0, 2](highBeamOn == 1))) ) \
                                    )\
                                ) and \
                                F[0, 10]( (turnSignal == 2) and \
                                    (((isLaneChanging == 1) implies (NearestNPCAhead >= 5)) and (isLaneChanging == 1) ) ) ))\
                    )'

    return traffic_rule

def prepare_for_rule50():
    # \begin{aligned}
    #     & G(speed \geq speedLimit.lowerLimit  \land \\
    #     & speed \leq speedLimit.upperLimit )
    # \end{aligned}    
    traffic_rule = '(always ((not (gear==2))))'
    return traffic_rule

# def prepare_for_rule51_3():
#     traffic_rule = "(always ((((((((trafficLightAheadcolor==3) and (direction==1)) and (Time<=20.0)) and (Time>=7.0))) -> ((turnSignal==1))) and (((((trafficLightAheadcolor==3) and (direction==1)) and (((Time>=20.0) or (Time<=7.0))))) -> (((turnSignal==1) and (lowBeamOn==1)))))))"
#     return traffic_rule

def prepare_for_rule51_4():
    traffic_rule = """(
    always (
        (
            (
                (trafficLightAheadcolor == 3)
                and
                (
                    (NPCAheadAhead <= 8.0) 
                    -> 
                    (eventually ((t1<=2) and (NPCAheadspeed > 0.5)))
                )
            )
            ->
            (
                (eventually ((t2 < 3) and (speed > 0.5)))
                and
                (not (NPCAheadAhead <= 0.5))
            )
        )
    )
)"""
    return traffic_rule

def prepare_for_rule51_5():
    traffic_rule = """(
    always (
        (
            (
                (trafficLightAheadcolor == 1)
                and
                (
                    (stoplineAhead <= 2.0)
                    or
                    (junctionAhead <= 2.0)
                    or
                    (NPCAheadAhead <= 0.5)
                )
            )
            ->
            (
                eventually ((t1<=2) and(speed < 0.5))
            )
        )
    )
)"""

    return traffic_rule

def prepare_for_rule51_6():
    traffic_rule = """(
    always (
        (
            (
                (direction == 2)
                and
                (NPCAheadAhead <= 2.0)
                and
                (eventually ((t1<=2) and (NPCAheadspeed < 0.5)))
            )
            ->
            (
                eventually ((t2<=3) and (speed < 0.5))
            )
        )
    )
)"""

    return traffic_rule

def prepare_for_rule51_7():
    traffic_rule = """(
    always(
        (
            (
                (direction == 2) or (direction == 1)
            )
            and
            (
                (PriorityNPCAhead == 1) or (PriorityPedsAhead == 1)
            )
        )
        -> 
        (
            eventually ((t1<=2) and (speed < 0.5))
        )
    )
)
"""

    return traffic_rule

def prepare_for_rule52():
    traffic_rule = "(\
                    always (\
                                ((signalAhead==0 and (NPCAheadAhead<=1)) and junctionAhead<=1.0) \
                                -> (eventually ((t1<=300) and (speed<0.5)))\
                            ) \
                    )"
    # traffic_rule = "(always (((((signalAhead==0 and ((NPCAheadAhead<=1 or PriorityPedsAhead<=1))) and junctionAhead<=1.0)) -> (eventually[0,200] (speed<0.5)))))"
    return traffic_rule

def prepare_for_rule53():
    traffic_rule = """(
    always(
        (
            (
                (isTrafficJam == 1)
                and
                (
                    (NPCAheadspeed < 0.5)
                    or
                    (NPCAheadAhead <= 0.5)
                    or
                    (junctionAhead <= 1.0)
                )
            )
            ->
            (
                eventually ((t1<=200) and (speed < 0.5))
            )
        )
    )
)
"""
    return traffic_rule


class PredicateCollector(StlAstVisitor):
    def __init__(self):
        self.predicates = []
        self.implies = []

        
    def visit(self, node, *args, **kwargs):
        if isinstance(node, Predicate):
            self.visit_predicate(node, args, kwargs)
        elif isinstance(node, Implies):
            self.visit_impies(node, args, kwargs)
        else:
            super().visit(node, *args, **kwargs)
        
    def visit_predicate(self, node, *args, **kwargs):
        op = str(node.operator)
        pre_str = node.name 
        lhs = pre_str[1:pre_str.find(op)-1]
        rhs = pre_str[pre_str.find(op)+len(op)+1:-1]
        self.predicates.append((lhs, op, rhs))
        # super().visit_predicate( node, args, kwargs)
    
    def visit_impies(self, node, *args, **kwargs):
        # print(node.name)
        lexpr = node.children[0]
        rexpr = node.children[1]
        self.implies.append((node, lexpr))
        
traffic_rules = {
    "rule38_1" : prepare_for_rule38_1(),
    "rule38_2" : prepare_for_rule38_2(),
    "rule38_3" : prepare_for_rule38_3(),
    "rule42" : prepare_for_rule42(),
    # "rule45" : prepare_for_rule45(),
    "rule46_2" : prepare_for_rule46_2(),
    "rule46_3" : prepare_for_rule46_3(),
    "rule50" : prepare_for_rule50(),
    "rule51_4" : prepare_for_rule51_4(),
    "rule51_5" : prepare_for_rule51_5(),
    "rule51_6" : prepare_for_rule51_6(),
    "rule51_7" : prepare_for_rule51_7(),
    "rule52" : prepare_for_rule52(),
    "rule53" : prepare_for_rule53(),

}

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

STR_TO_BINOP = {
    "==": operator.eq,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt
}

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


def parse_law(law_str):

    spec = rtamt.StlDenseTimeSpecification(semantics=rtamt.Semantics.STANDARD)

    for item in VARIABLE_APIS:
        spec.declare_var(item, 'float')
    spec.declare_var("t1", "int")
    spec.declare_var("t2", "int")
    # also need to know what is the precondition for t1 and t2
    
    spec.spec = law_str
    spec.parse()
    
    ast = spec.ast.specs[0]

    collector = PredicateCollector()
    collector.visit(ast)
    
    return collector.predicates

for r in traffic_rules:
    parse_law(traffic_rules[r])

exit(0)


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
        self.predicates = parse_law(traffic_rules[rule])
        self.rule = rule
        
        self.predicates = sorted(self.predicates)
        
        self.state_space=sorted(list(self.enumerate_possible_states()))
        self.state_idx = None
        self.state_interpretation = None

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
    
