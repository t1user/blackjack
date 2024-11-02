from __future__ import annotations

import random
from typing import Any

from .engine import BettingStrategy, GameStrategy, Hand, PlayDecision


class RandomStrategy(GameStrategy):

    def play(
        self, dealer_hand: Hand, player_hand: Hand, choices: PlayDecision
    ) -> PlayDecision:
        return random.choice(list(choices))

    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choice((True, False))


class MimickDealer(GameStrategy):

    def play(
        self, dealer_hand: Hand, player_hand: Hand, choices: PlayDecision
    ) -> PlayDecision:
        return PlayDecision.HIT if player_hand.value < 18 else PlayDecision.STAND

    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choice((True, False))


class FixedBettingStrategy(BettingStrategy):
    def __init__(self, betsize: float) -> None:
        self.betsize = betsize

    def bet(self, *args: Any, **kwargs: Any) -> float:
        return self.betsize

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.betsize})"
