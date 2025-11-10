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

class AtomicPredicate(BaseModel):
    neg: bool = False
    lhs : str
    op : Literal['==', '!=', '>', '<', '>=', '<=']
    rhs : Any
    
    def __str__(self):
        n = "!" if self.neg else ""
        return f"{n}({self.lhs} {self.op} {self.rhs})"
    
    def state_eval(self, observation):
        op = OP_MAP[self.op] if self.neg else OP_MAP[NEGATE_OP[self.op]]
        return op(observation[self.lhs], self.rhs)
    
    
class BinaryPredicate(BaseModel):
    lhs: Any 
    op: Literal["and", "or"]
    rhs: Any
    
    def __str__(self):
        return f"({self.lhs}) {self.op} ({self.rhs})"
    
    def state_eval(self, observation):
        return eval(self.lhs, observation) and eval(self.rhs, observation) if self.op == "and"\
            else eval(self.lhs, observation) or eval(self.rhs, observation)
    
class QuantifiedPredicate(BaseModel):
    quantifier: Literal["exist", "all"]
    predicate : Union[AtomicPredicate , BinaryPredicate ]
    
    def __str__(self):
        return f"{self.quantifier} {str(self.predicate)}"
    
    def state_eval(self, observations: List[Any]):
        if self.quantifier == "exist":
            return any(self.predicate.state_eval(o) for o in observations)
        else:    
            return all(self.predicate.state_eval(o) for o in observations)