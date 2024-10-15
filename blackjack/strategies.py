from __future__ import annotations

import random
from abc import ABC, abstractmethod
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Literal

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

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}()"


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

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}()"


class BettingStrategy(ABC):

    @abstractmethod
    def bet(self, *args: Any, **kwargs: Any) -> float:
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}()"


class FixedBettingStrategy(BettingStrategy):
    def __init__(self, betsize: float) -> None:
        self.betsize = betsize

    def bet(self, *args: Any, **kwargs: Any) -> float:
        return self.betsize

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.betsize})"
