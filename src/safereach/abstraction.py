from abc import ABC, abstractmethod
from typing import Any, Set, List, Mapping

FINISH = "finish"

class Abstraction(ABC):

    @abstractmethod
    def get_state_idx(self, states) -> Mapping[str, int]:
        pass

    @abstractmethod
    def get_state_interpretation(self, states) -> Mapping[str, Mapping[str, bool]]:
        pass

    @abstractmethod
    def encode(self, observations: List[Any]) -> str:
        pass

    @abstractmethod
    def decode(self, state: str) -> List[Any]:
        pass

    @abstractmethod
    def valid_trans(self, state1: str, state2: str) -> bool:
        pass
    