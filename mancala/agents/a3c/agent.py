from mancala.rule import Rule
from typing import Union

import numpy as np
import torch
import torch.nn.functional as F
from gym.utils import seeding
from gym import spaces
from torch.autograd import Variable

from mancala.agents.base import BaseAgent
from mancala.state.base import BaseState
from mancala.agents.a3c.model import ActorCritic


class A3CAgent(BaseAgent):
    """Agent which leverages Actor Critic Learning"""

    def __init__(
        self, id: int, model_path: str = "", model: Union[ActorCritic, None] = None
    ):
        self.deterministic = False
        self._seed = 42
        self.id = id

        self.np_random, _ = seeding.np_random(self._seed)
        if torch.cuda.is_available():
            self._dtype = torch.cuda.FloatTensor
        else:
            self._dtype = torch.FloatTensor

        rule = Rule()

        def init_board(rule: Rule) -> np.ndarray:
            board = np.zeros(((rule.pockets + 1) * 2,), dtype=np.int32)
            # Player 1 side
            for i in range(0, rule.pockets):
                board[i] = rule.initial_stones
            # Player 2 side
            for i in range(rule.pockets + 1, rule.pockets * 2 + 1):
                board[i] = rule.initial_stones
            return board

        board = init_board(rule)
        action_space = spaces.Discrete(6)
        if model is None:
            self._model = ActorCritic(board.shape[0], action_space).type(self._dtype)
            if model_path:
                self._model.load_state_dict(torch.load(model_path))
        else:
            self._model = model

    def policy(self, state: BaseState) -> Union[int, None]:
        """Return move which ends in score hole"""
        assert not state.is_terminal()
        assert self.id == state.current_player
        clone = state.clone()
        move_options = state.legal_actions(state.current_player)
        if move_options is None:
            return None

        board = torch.from_numpy(clone.board).type(self._dtype)
        cx = Variable(torch.zeros(1, 400).type(self._dtype))
        hx = Variable(torch.zeros(1, 400).type(self._dtype))

        with torch.no_grad():
            _, logit, (hx, cx) = self._model((Variable(board.unsqueeze(0)), (hx, cx)))
        prob = F.softmax(logit, dim=0)
        scores = [
            (action, score)
            for action, score in enumerate(prob[0].data.tolist())
            if action in move_options
        ]

        valid_actions = [action for action, _ in scores]
        valid_scores = np.array([score for _, score in scores])

        final_move = self.np_random.choice(
            valid_actions, 1, p=valid_scores / valid_scores.sum()
        )[0]
        return final_move
