from pydantic import BaseModel
from typing import Any, Literal, List, Union

from rtamt.syntax.node.ltl.neg import Neg
from rtamt.syntax.node.ltl.predicate import Predicate
from rtamt.syntax.node.ltl.conjunction import Conjunction
from rtamt.syntax.node.ltl.disjunction import Disjunction
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
        
        
def convert(node):
    """
    Convert STL/AST predicate nodes (Conjunction, Disjunction, Atomic)
    into BinaryPredicate or AtomicPredicate (Pydantic models).
    """
    
    # Base case: Atomic predicate
    if isinstance(node, Predicate):
        return AtomicPredicate(
            neg = False,
            lhs = node.children[0].name,
            op  = str(node.operator),
            rhs = node.children[1].val
        )
    
    # Negation case (if your AST has it)
    if isinstance(node, Neg):
        inner = convert(node.child)
        if isinstance(inner, AtomicPredicate):
            # Flip atomic neg flag
            return AtomicPredicate(
                neg = not inner.neg,
                lhs = inner.lhs,
                op  = inner.op,
                rhs = inner.rhs
            )
        else:
            # Wrap binary predicate in a new negation binary node if needed
            # (depends on your language semantics)
            raise NotImplementedError("Negation of binary predicates not supported")

    # Conjunction → BinaryPredicate(lhs, "and", rhs)
    if isinstance(node, Conjunction):
        print(node.name)
        print("Conjunction")
        return BinaryPredicate(
            lhs = convert(node.children[0]),
            op  = "and",
            rhs = convert(node.children[1]),
        )
    
    # Disjunction → BinaryPredicate(lhs, "or", rhs)
    if isinstance(node, Disjunction):
        print(node.name)
        print("Disjunction")
        return BinaryPredicate(
            lhs = convert(node.children[0]),
            op  = "or",
            rhs = convert(node.children[1])
        )

    raise TypeError(f"Unknown node type: {type(node)}")
