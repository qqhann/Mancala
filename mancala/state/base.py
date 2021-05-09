from abc import ABC
from builtins import NotImplementedError
from typing import List


class BaseState(ABC):
    action_choices: List[str]

    def __repr__(self):
        raise NotImplementedError

    def clone(self):
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseState):
            return NotImplemented
        raise NotImplementedError

    @property
    def current_player(self) -> int:
        raise NotImplementedError

    def legal_actions(self, turn: int):
        raise NotImplementedError
