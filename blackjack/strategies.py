from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import Hand


class GameStrategy(ABC):

    @abstractmethod
    def insurance(self, dealer_hand: Hand, player_hand: Hand | None) -> bool: ...

    @abstractmethod
    def split(self, dealer_hand: Hand, player_hand: Hand | None) -> bool: ...

    @abstractmethod
    def double(self, dealer_hand: Hand, player_hand: Hand | None) -> bool: ...

    @abstractmethod
    def hit(self, dealer_hand: Hand, player_hand: Hand | None) -> bool: ...


class DealerStrategy(GameStrategy):
    def insurance(self, dealer_hand: Hand, player_hand: Hand | None = None) -> bool:
        raise NotImplementedError

    def split(self, dealer_hand: Hand, player_hand: Hand | None = None) -> bool:
        raise NotImplementedError

    def double(self, dealer_hand: Hand, player_hand: Hand | None = None) -> bool:
        raise NotImplementedError

    def hit(self, dealer_hand: Hand, player_hand: Hand | None) -> bool:
        return dealer_hand.soft_value < 17


class RandomStrategy(GameStrategy):
    def insurance(self, dealer_hand: Hand, player_hand: Hand | None) -> bool:
        return random.choice((True, False))

    def split(self, dealer_hand: Hand, player_hand: Hand | None) -> bool:
        return random.choice((True, False))

    def double(self, dealer_hand: Hand, player_hand: Hand | None) -> bool:
        return random.choice((True, False))

    def hit(self, dealer_hand: Hand, player_hand: Hand | None) -> bool:
        return random.choice((True, False))
