from pydantic import BaseModel
from typing import Any, Literal, List, Union
# We assume this predicate would evaluate on the observations {k:v} using observation[lhs] op rhs


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

class StatePredicate(BaseModel):
    pass

class AtomicPredicate(StatePredicate):
    neg: bool = False
    lhs : str
    op : Literal['==', '!=', '>', '<', '>=', '<=']
    rhs : Any
    
    def __str__(self):
        n = "!" if self.neg else ""
        return f"{n}({self.lhs} {self.op} {self.rhs})"
    
    def state_eval(self, observation):
        op = OP_MAP[self.op] if not self.neg else OP_MAP[NEGATE_OP[self.op]]
        return op(observation[self.lhs], self.rhs)
    
    
class BinaryPredicate(StatePredicate):
    lhs: Any 
    op: Literal["and", "or"]
    rhs: Any
    
    def __str__(self):
        return f"({self.lhs}) {self.op} ({self.rhs})"
    
    def state_eval(self, observation): 
        # print(self.lhs)
        # print(self.lhs.state_eval(observation))
        # print(self.rhs)
        # print(observation["parentReceptacles"])
        # print(self.rhs.state_eval(observation))
        return self.lhs.state_eval(observation) and self.rhs.state_eval( observation) if self.op == "and"\
            else self.lhs.state_eval( observation) or self.rhs.state_eval(observation)
    
class QuantifiedPredicate(StatePredicate):
    quantifier: Literal["exist", "all"]
    predicate : Union[AtomicPredicate , BinaryPredicate]
    
    def __str__(self):
        return f"{self.quantifier} {str(self.predicate)}"
    
    def state_eval(self, observations: List[Any]):
        if self.quantifier == "exist":
            return any(self.predicate.state_eval(o) for o in observations)
        else:    
            return all(self.predicate.state_eval(o) for o in observations)