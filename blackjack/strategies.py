from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .engine import Hand


class GameStrategy(ABC):

    @abstractmethod
    def surrender(self, dealer_hand: Hand, player_hand: Hand) -> bool: ...

    @abstractmethod
    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool: ...

    @abstractmethod
    def split(self, dealer_hand: Hand, player_hand: Hand) -> bool: ...

    @abstractmethod
    def double(self, dealer_hand: Hand, player_hand: Hand) -> bool: ...

    @abstractmethod
    def hit(self, dealer_hand: Hand, player_hand: Hand) -> bool: ...


class RandomStrategy(GameStrategy):
    def surrender(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choices((True, False), (0.2, 0.8))[0]

    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choice((True, False))

    def split(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choices((True, False), (0.7, 0.3))[0]

    def double(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choices((True, False), (0.8, 0.2))[0]

    def hit(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choice((True, False))


class MimickDealer(GameStrategy):
    def surrender(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choices((True, False), (0.2, 0.8))[0]

    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choice((True, False))

    def split(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choices((True, False), (0.7, 0.3))[0]

    def double(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return random.choices((True, False), (0.8, 0.2))[0]

    def hit(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return player_hand.soft_value <= 17


class DealerStrategy:
    def hit(self, dealer_hand: Hand) -> bool:
        return dealer_hand.soft_value < 17


class BettingStrategy(ABC):

    @abstractmethod
    def bet(self, *args: Any, **kwargs: Any) -> float:
        pass


class FixedBettingStrategy:
    def __init__(self, betsize: float) -> None:
        self.betsize = betsize

    def bet(self, *args: Any, **kwargs: Any):
        return self.betsize
