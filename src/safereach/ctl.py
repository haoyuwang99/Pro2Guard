from pydantic import BaseModel
from typing import Any

class PathFormula(BaseModel):
    pass
    
class Until(PathFormula):
    predicate1 : Any
    predicate2 : Any
    
    def __str__(self):
        return f"{self.predicate1} U {self.predicate2}"
    
class Next(PathFormula):
    predicate: Any
    
    def __str__(self):
        return f"X {self.predicate}"
    
class Finally(PathFormula):
    predicate: Any
    bound: int = -1 # -1 indicate no bound
    
    def __str__(self):
        bound = "" if self.bound <=0 else f"<={self.bound}"
        return f"F{bound} {self.predicate}"
    
class Always(PathFormula):
    predicate: Any
    bound: int = -1 # -1 indicate no bound
    
    def __str__(self):
        bound = "" if self.bound <=0 else f"<={self.bound}"
        return f"G{bound} {self.predicate}"
    
class All(BaseModel):
    formula: PathFormula
    
class Exist(BaseModel):
    formula: PathFormula
    