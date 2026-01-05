from pydantic import BaseModel
from typing import Any, Literal, List, Union

# from rtamt.syntax.node.ltl.neg import Neg
# from rtamt.syntax.node.ltl.predicate import Predicate
# from rtamt.syntax.node.ltl.conjunction import Conjunction
# from rtamt.syntax.node.ltl.disjunction import Disjunction
# from rtamt.syntax.node.stl.timed_eventually import TimedEventually
# We assume this predicate would evaluate on the observations {k:v} using observation[lhs] op rhs

def convert_to_bool_var(lhs, op, rhs): 
    return f"{lhs}_{op}_{rhs}"


OP_MAP = {
    '==': lambda a, b: a == b,
    '!=': lambda a, b: a != b,
    '>':  lambda a, b: a > b,
    '<':  lambda a, b: a < b,
    '>=': lambda a, b: a >= b,
    '<=': lambda a, b: a <= b
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


class AtomicPredicate(BaseModel):
    neg: bool = False
    lhs : str
    op : Literal['==', '!=', '>', '<', '>=', '<=', "in"]
    rhs : Any
    
    def __str__(self):
        n = "!" if self.neg else ""
        return f"{n}({self.lhs} {self.op} {self.rhs})"
    
    def state_eval(self, observation):
        if self.op == "in":
            # specifically for list
            # print(observation[self.lhs])
            return observation[self.lhs] != None and self.rhs in observation[self.lhs]
        op = OP_MAP[self.op] if not self.neg else OP_MAP[NEGATE_OP[self.op]]
        # print(observation[self.lhs],", ", self.rhs)
        return op(observation[self.lhs], self.rhs)
    
    
class BinaryPredicate(BaseModel):
    lhs: Any 
    op: Literal["and", "or"]
    rhs: Any
    
    def __str__(self):
        return f"({self.lhs}) {self.op} ({self.rhs})"
    
    def state_eval(self, observation): 
        # print
        # print(self.lhs)
        # print(self.lhs.state_eval(observation))
        # print(self.rhs)
        # print(observation["parentReceptacles"])
        # print(self.rhs.state_eval(observation))
        return self.lhs.state_eval(observation) and self.rhs.state_eval( observation) if self.op == "and"\
            else self.lhs.state_eval( observation) or self.rhs.state_eval(observation)
    
class QuantifiedPredicate(BaseModel):
    quantifier: Literal["exist", "all"]
    predicate : Union[AtomicPredicate , BinaryPredicate]
    
    def __str__(self):
        return f"{self.quantifier} {str(self.predicate)}"
    
    def state_eval(self, observations: List[Any]):
        if self.quantifier == "exist":
            return any(self.predicate.state_eval(o) for o in observations)
        else:    
            return all(self.predicate.state_eval(o) for o in observations)
        
        
# def convert(node):
#     """
#     Convert STL/AST predicate nodes (Conjunction, Disjunction, Atomic)
#     into BinaryPredicate or AtomicPredicate (Pydantic models).
#     """
    
#     # Base case: Atomic predicate
#     if isinstance(node, Predicate):
#         return AtomicPredicate(
#             neg = False,
#             lhs = node.children[0].name,
#             op  = str(node.operator),
#             rhs = node.children[1].val
#         )
    
#     # Negation case (if your AST has it)
#     if isinstance(node, Neg):
#         inner = convert(node.children[0])
#         if isinstance(inner, AtomicPredicate):
#             # Flip atomic neg flag
#             return AtomicPredicate(
#                 neg = not inner.neg,
#                 lhs = inner.lhs,
#                 op  = inner.op,
#                 rhs = inner.rhs
#             )
#         else:
#             # Wrap binary predicate in a new negation binary node if needed
#             # (depends on your language semantics)
#             raise NotImplementedError("Negation of binary predicates not supported")

#     # Conjunction → BinaryPredicate(lhs, "and", rhs)
#     if isinstance(node, Conjunction):

#         return BinaryPredicate(
#             lhs = convert(node.children[0]),
#             op  = "and",
#             rhs = convert(node.children[1]),
#         )
    
#     # Disjunction → BinaryPredicate(lhs, "or", rhs)
#     if isinstance(node, Disjunction):

#         return BinaryPredicate(
#             lhs = convert(node.children[0]),
#             op  = "or",
#             rhs = convert(node.children[1])
#         )

#     raise TypeError(f"Unknown node type: {type(node)}")

# def parse_K_eventually(node):
    # if isinstance(node, TimedEventually):
    #     inner = node.children[0]
    #     K = node.end
    #     return (inner, K)
    # raise TypeError("upsupported type: ", type(node))
    
def truth_table(interp, pred):
    if interp=="finish":
        return False
    if type(pred)== QuantifiedPredicate:
        # print(interp)
        pred_name = str(pred)
        pred_value = interp[pred_name] 
        if pred_name not in interp:
            print("Not in keys: ", pred_name)
        # print(pred, pred_value)
        return pred_value
    elif type(pred)==AtomicPredicate:
        # print
        # print(pred)
        pred_name = convert_to_bool_var(pred.lhs, pred.op, pred.rhs)
        pred_value = interp[pred_name]
        return pred_value
    elif type(pred) == BinaryPredicate:
        lval = truth_table(interp, pred.lhs) 
        rval = truth_table(interp, pred.rhs) 
        # print(pred, lval, rval)
        if pred.op == "and":
            return lval and rval
        else:
            return lval or rval
    else:

        raise Exception(f"Unsupported type")
    
# this returns the states that satisfy the pred
# state_interp is mapping from atomic/quantified predicate to its boolean observation
def filter(state_interp, pred):
    # print(state_interp)
    
    states = []
    for s in state_interp:
        if truth_table(state_interp[s], pred):
            states.append(s)
    return states
