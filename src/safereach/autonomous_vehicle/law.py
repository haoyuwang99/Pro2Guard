import rtamt
import operator

from rtamt.syntax.node.ltl.predicate import Predicate
from rtamt.syntax.node.ltl.eventually import Eventually
from rtamt.syntax.node.ltl.always import Always
from rtamt.syntax.node.ltl.implies import Implies
# from rtamt.syntax.node.ltl.binary_node import BinaryNode
from rtamt.syntax.ast.visitor.stl.ast_visitor import StlAstVisitor
from rtamt.syntax.node.ltl.conjunction import Conjunction
from rtamt.syntax.node.ltl.disjunction import Disjunction

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
    

        
def prepare_for_rule38_1():              
    #GREEN = 3; 
    traffic_rule = '(\
                            always( (   (   (trafficLightAheadcolor == 3) and \
                                            (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)    ) \
                                implies (eventually[0,100](speed > 0.5)) ) \
                            )\
                    )'
    return traffic_rule

def prepare_for_rule38_2():              
    #YELLOW = 2;
    traffic_rule = '(\
                            always(\
                                    ( \
                                        (\
                                            (trafficLightAheadcolor == 2) and ((currentLanenumber == 0))\
                                        ) implies ( eventually[0,100](speed > 0.5) )\
                                    ) and \
                                    ( \
                                        (\
                                            (trafficLightAheadcolor == 2) and ((currentLanenumber > 0))\
                                        ) implies ( eventually[0,100](speed < 0.5) )\
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
                                implies ( eventually[0,100](speed < 0.5) )) and \
                                (((trafficLightAheadcolor == 1) and \
                                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
                                (direction == 2) and (PriorityNPCAhead == 0) and \
                                (currentLanenumber > 0) and \
                                (PriorityPedsAhead == 0) ) \
                                implies ( eventually[0,100](speed > 0.5) )) ) \
                            )'
    return traffic_rule

def prepare_for_rule38():              
    # message TrafficLight {
    #   enum Color {
    #     UNKNOWN = 0;
    #     RED = 1;
    #     YELLOW = 2;
    #     GREEN = 3;
    #     BLACK = 4;
    #   };       
    # we should put different weight on different variables!
    traffic_rule = '(always(((trafficLightAheadcolor == 3) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)) implies ( speed >= 0.1 ))   and \
                            always((((trafficLightAheadcolor == 2) and ((stoplineAhead == 0) or (stoplineAhead > 50))) implies ( speed > 0.1 )) and \
                                    (((trafficLightAheadcolor == 2) and (stoplineAhead <= 2)) implies (speed < 0.1)) ) and \
                            always((((trafficLightAheadcolor == 1) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (direction <= 1)) implies ( speed < 0.1 )) and \
                                    (((trafficLightAheadcolor == 1) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (direction == 2) and (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0) ) implies ( speed >= 0.1 )) ) \
                            )'
    return traffic_rule

def prepare_for_rule42():
    # \begin{aligned}
    #     & G(((trafficLightAhead.color = yellow \land \\
    #     & trafficLightAhead.blink) \lor \\
    #     & (trafficLightAhead.direction.color = yellow \land \\
    #     & trafficLightAhead.direction.blink)) \land \\
    #     & ( stoplineAhead(realvalue) \lor junctionAhead(realvalue) )\\
    #     & \implies    speed < realvalue )
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

def prepare_for_rule51_3():
    traffic_rule = "(always ((((((((trafficLightAheadcolor==3) and (direction==1)) and (Time<=20.0)) and (Time>=7.0))) -> ((turnSignal==1))) and (((((trafficLightAheadcolor==3) and (direction==1)) and (((Time>=20.0) or (Time<=7.0))))) -> (((turnSignal==1) and (lowBeamOn==1)))))))"
    return traffic_rule

def prepare_for_rule51_4():
    traffic_rule = "(always ((((trafficLightAheadcolor==3) and (((not (NPCAheadAhead<=8.0)) or (((((NPCAheadAhead<=8.0) -> (eventually[0,2] ((NPCAheadspeed>0.5))))) and (NPCAheadAhead<=8.0)))))) -> (((eventually[0,3] ((speed>0.5)))) and (not (NPCAheadAhead<=0.5))))))"
    return traffic_rule

def prepare_for_rule51_5():
    traffic_rule = "(always ((((trafficLightAheadcolor==1) and ((((stoplineAhead<=2.0) or (junctionAhead<=2.0)) or (NPCAheadAhead<=0.5)))) -> (eventually[0,2] ((speed<0.5))))))"
    return traffic_rule

def prepare_for_rule51_6():
    traffic_rule = "(always ((((((direction==2) and (NPCAheadAhead<=2.0)) and ((eventually[0,2] ((NPCAheadspeed<0.5)))))) -> (eventually[0,3] ((speed<0.5))))))"
    return traffic_rule

def prepare_for_rule51_7():
    traffic_rule = "(always (((((((direction==2) or (direction==1))) and (((PriorityNPCAhead==1) or (PriorityPedsAhead==1))))) -> (eventually[0,2] ((speed<0.5))))))"
    return traffic_rule

def prepare_for_rule52():
    traffic_rule = "(\
                    always (\
                                ((signalAhead==0 and (NPCAheadAhead<=1)) and junctionAhead<=1.0) \
                                -> (eventually[0,300] (speed<0.5))\
                            ) \
                    )"
    # traffic_rule = "(always (((((signalAhead==0 and ((NPCAheadAhead<=1 or PriorityPedsAhead<=1))) and junctionAhead<=1.0)) -> (eventually[0,200] (speed<0.5)))))"
    return traffic_rule

def prepare_for_rule53():
    traffic_rule = "(always ((((isTrafficJam==1 and (((NPCAheadspeed<0.5 or NPCAheadAhead<=0.5) or junctionAhead<=1.0)))) -> (eventually[0,200] (speed<0.5)))))"
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
            
        super().visit(node, *args, **kwargs)
        
    def visit_predicate(self, node, *args, **kwargs):
        op = str(node.operator)
        pre_str = node.name 
        lhs = pre_str[1:pre_str.find(op)-1]
        rhs = pre_str[pre_str.find(op)+len(op)+1:-1]
        self.predicates.append((lhs, op, rhs))
        # super().visit_predicate( node, args, kwargs)
    
    def visit_impies(self, node, *args, **kwargs):
        # print("====")
        # print(node.name)
        # print("====")
        lexpr = node.children[0]
        rexpr = node.children[1] 
        self.implies.append((lexpr, rexpr))
        
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

def eval_temoral(traj, i, node):
    pass

    # else:
    #     print(type(node))
    #     raise Exception("unsupported type")

def eval_node(traj, i, node):   
    if type(node) == Conjunction:
        return eval_node(traj, i, node.children[0]) and eval_node(traj, i, node.children[1])
    elif type(node) == Disjunction:
        return eval_node(traj, i, node.children[0]) or eval_node(traj, i, node.children[1])
    elif type(node) == Implies:
        # print(node.children[0].name)     
        # print(not eval_node(traj, i, node.children[0]) )
        # print("=>")
        # print(node.children[1])
        return not eval_node(traj, i, node.children[0]) or eval_node(traj, i, node.children[1])
    elif type(node) == Predicate:
        observation = traj[i]
        op = str(node.operator)
        pre_str = node.name 
        lhs = pre_str[1:pre_str.find(op)-1]
        rhs = pre_str[pre_str.find(op)+len(op)+1:-1]
        return eval_pred(observation, (lhs, op, rhs))
    elif type(node) == Eventually:
        return any(eval_node(traj, j, node.children[0]) for j in range(i,len(traj)))
    elif type(node) == Always:
        return all(eval_node(traj, j, node.children[0]) for j in range(i,len(traj)))
    else: 
        print(type(node))
        raise Exception("unsupported node type")

def translate_to_pctl(law_str):
    pass

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
    
    return collector

for r in traffic_rules:
    parse_law(traffic_rules[r])
