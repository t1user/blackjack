from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property, partial, wraps
from typing import Any, Callable, Literal, Self

from .strategies import BettingStrategy, DealerStrategy, GameStrategy

# ### Rules ###
MAX_SPLITS = -1  # negative number means no limit
RESPLIT_ACES = False
BURN_PERCENT_RANGE = (20, 25)  # penetration percentage range (min, max)
NUMBER_OF_DECKS = 6
PLAYER_CASH = 1_000
# ### End-rules ###

SUITS = ["S", "H", "D", "C"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
FACES = ["10", "J", "Q", "K"]

suit_str_dict = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}


class Suit(str, Enum):
    S = "♠"
    H = "♥"
    D = "♦"
    C = "♣"


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    def __new__(cls, rank: str, suit: str) -> Self:
        try:
            assert rank in RANKS, f"rank must be one of {RANKS}, not {rank}"
            assert suit in SUITS, f"suit must be one of {SUITS}, not {suit}"
        except AssertionError as e:
            raise ValueError(f"Wrong value -> {e.__context__}>") from e
        return super().__new__(cls)

    @cached_property
    def value(self):
        if self.is_face:
            return 10
        elif self.is_ace:
            return 11
        else:
            return int(self.rank)

    @cached_property
    def soft_value(self):
        if not self.is_ace:
            return self.value
        else:
            return 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return (self.rank == other.rank) or (self.is_face and other.is_face)

    @property
    def is_ace(self) -> bool:
        return self.rank == "A"

    @property
    def is_face(self) -> bool:
        return self.rank in FACES

    def __str__(self) -> str:
        return f"{self.rank}{suit_str_dict.get(self.suit)}"


DECK = [Card(rank, suit) for rank in RANKS for suit in SUITS]


class Shoe(list[Card]):

    def __init__(self, decks: int):
        super().__init__()
        self.decks = decks
        self._cut_card: int = 0
        self.shuffle()

    def will_shuffle(self) -> bool:
        if len(self) < self._cut_card:
            return True
        else:
            return False

    def shuffle(self) -> None:
        self.extend([*DECK * self.decks])
        random.shuffle(self)
        self._cut_cardcut_card = int(
            random.randint(*BURN_PERCENT_RANGE) * len(self) / 100
        )

    def deal(self) -> Card:
        return self.pop()

    def __str__(self) -> str:
        return "[" + ", ".join(map(str, self)) + "]"


class Hand(list[Card]):
    """
    Container for cards with methods calculating hand value and comparing it with other
    hands.
    """

    def __init__(self, *cards: Card) -> None:
        super().__init__(cards)

    @property
    def value(self) -> int:
        if (v := max(self.hard_value, (sv := self.soft_value))) <= 21:
            return v
        else:
            return sv

    @property
    def hard_value(self) -> int:
        return sum([card.value for card in self])

    @property
    def soft_value(self) -> int:
        return sum([card.soft_value for card in self])

    def is_bust(self) -> bool:
        return self.value > 21

    def _has_face(self) -> bool:
        return any([card.is_face for card in self])

    def _has_ace(self) -> bool:
        return any([card.rank == "A" for card in self])

    def is_double_aces(self) -> bool:
        return all([card.is_ace for card in self])

    def is_blackjack(self) -> bool:
        return (len(self) == 2) and self._has_face() and self._has_ace()

    def can_split(self) -> bool:
        return (len(self) == 2) and (
            (self[0].rank == self[1].rank)
            or all([(card.rank in FACES) for card in self])
        )

    def value_str(self) -> str:
        if (hv := self.hard_value) != (sv := self.soft_value):
            return f"{hv}/{sv}"
        else:
            return str(sv)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return NotImplemented
        elif all((self.is_blackjack(), other.is_blackjack())):
            return True
        elif any((self.is_blackjack(), other.is_blackjack())):
            return False
        else:
            return self.value == other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return NotImplemented
        elif self.is_blackjack() and not other.is_blackjack():
            return True
        elif not self.is_blackjack() and other.is_blackjack():
            return False
        else:
            return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return NotImplemented
        else:
            return (self > other) or (self == other)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return NotImplemented
        elif not self.is_blackjack() and other.is_blackjack():
            return True
        elif self.is_blackjack() and not other.is_blackjack():
            return False
        else:
            return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return NotImplemented
        else:
            return (self < other) or (self == other)

    def __iadd__(self, card: Card) -> Self:  # type: ignore
        self.append(card)
        return self

    def __str__(self) -> str:
        return ", ".join(map(str, self))


@dataclass
class HandPlay:
    """
    Container for all information relevant to how a Hand is played and methods
    evaluating wheather play was won or lost.
    """

    betsize: int
    player: "Player"
    hand: Hand = field(default_factory=Hand)
    insurance: bool = False
    splits: int = 0
    _is_done: bool = field(init=False, default=False, repr=False)

    def __post_init__(self):
        pass

    def charge_bet(self) -> None:
        self.player.charge(self.betsize)

    @property
    def is_done(self) -> bool:

        return (
            # no resplits on double aces
            (bool(self.splits) and self.hand.is_double_aces())
            # is blackjack
            or self.hand.is_blackjack()
            # is 21
            or self.hand.value == 21
            # has manually been set to done
            or self._is_done
        )

    def done(self) -> None:
        self._is_done = True

    def surrender(self, *args) -> Literal[-1, 0, 1]:
        pass

    def insure(self, dealer_hand: Hand) -> None:
        if self.player.strategy.insurance(dealer_hand, self.hand):
            self.player.cash.charge(self.betsize)
            self.insurance = True

    def eval_hand(self, dealer_hand: Hand) -> Literal[-1, 0, 1]:
        if self.hand > dealer_hand:
            return 1
        elif self.hand < dealer_hand:
            return -1
        elif self.hand == dealer_hand:
            return 0
        else:
            raise ValueError("How the fuck did we get here?")

    def eval_insurance(self, dealer_hand: Hand) -> Literal[-1, 0, 1]:
        if dealer_hand.is_blackjack():
            return 1.5
        else:
            return -1

    def __iadd__(self, card: Card) -> Self:
        self.hand.append(card)
        return self

    def can_split(self):
        if self.is_done or (self.splits > MAX_SPLITS):
            return False
        else:
            return self.hand.can_split()

    @classmethod
    def split(
        cls, bet_size: int, player: Player, hand: Hand, splits: int, **kwargs: Any
    ) -> list[Self]:
        return [
            cls(bet_size, player, Hand(card), splits=splits + 1, **kwargs)
            for card in hand
        ]


class NotEnoughCash(Exception):
    pass


class Cash:

    def __init__(self, balance: float):
        if balance < 0:
            raise ValueError("Initial cash value must be greater than zero.")
        self.balance = balance

    def check_amount(self, amount: float) -> float:
        if amount > self.balance:
            raise NotEnoughCash("Not enough cash")
        else:
            return amount

    def charge(self, amount: float) -> float:
        self.balance -= self.check_amount(amount)
        return self.balance

    def credit(self, amount: float) -> float:
        self.balance += amount
        return self.balance

    __iadd__ = credit
    __isub__ = charge

    def __eq__(self, value: object) -> bool:
        return self.balance == value


@dataclass
class Dealer:
    shoe: Shoe = field(default_factory=partial(Shoe, NUMBER_OF_DECKS))
    hand: Hand = field(default_factory=Hand)
    game_strategy: DealerStrategy = DealerStrategy()

    def deal(self, hand: Hand):
        hand += self.shoe.pop()

    def shuffle(self):
        if self.shoe.will_shuffle():
            self.shoe.shuffle()

    def table_deal(self):
        pass


@dataclass
class Player:
    strategy: GameStrategy
    betting_strategy: BettingStrategy
    cash: Cash = field(default_factory=partial(Cash, PLAYER_CASH))

    @property
    def will_continue(self) -> bool:
        return True

    def charge(self, amount: float) -> None:
        self.cash.charge(amount)

    def credit(self, amount: float) -> None:
        self.cash.credit(amount)


# DECIDE HOW YOU WANT CASH HANDLED, IT'S NOT DONE


@dataclass
class Table:
    hands: list[HandPlay] = field(default_factory=list)

    @staticmethod
    def all_hands(func: Callable[..., bool | None]) -> Callable[..., bool | None]:
        """
        Decorator, which if applied to a method, will call this method on all objects in
        self.hands.
        """

        @wraps(func)
        def wrapper(self: Table, dealer: Dealer) -> None:
            # self.hands may be modified during iteration!
            # works now but careful!
            for hand_play in self.hands:
                func(dealer, hand_play)

        return wrapper

    @staticmethod
    def check_if_done_first(
        func: Callable[..., bool | None]
    ) -> Callable[..., bool | None]:
        """
        Decorator, which will cause the method to immediately return if it's applied
        on a HandPlay object with .is_done property evaluating to True.
        """

        @wraps(func)
        def wrapper(self: Table, dealer: Dealer, hand_play: HandPlay):
            if hand_play.is_done:
                return None
            else:
                return func(self, dealer, hand_play)

        return wrapper

    @staticmethod
    def charge_bet(func: Callable[..., None | bool]) -> Callable[..., None | bool]:

        @wraps(func)
        def wrapper(self: Table, dealer: Dealer, hand_play: HandPlay):
            try:
                hand_play.player.cash.check_amount(hand_play.betsize)
            except NotEnoughCash:
                return

            if func(dealer, hand_play):
                hand_play.player.cash.charge(hand_play.betsize)

        return wrapper

    @all_hands
    def insurance(self, dealer: Dealer, hand_play: HandPlay) -> bool:
        if hand_play.player.strategy.insurance(dealer.hand, hand_play.hand):
            # check if cash available
            hand_play.player.cash.charge(hand_play.betsize)
            hand_play.insurance = True
            return True
        return False

    @charge_bet
    @check_if_done_first
    def play(self, dealer: Dealer, hand_play: HandPlay) -> None:
        # surender?
        # split
        number_of_hands_before = len(self.hands)
        self.split(dealer, hand_play)
        if len(self.hands) != number_of_hands_before:
            return
        # double
        self.double(dealer, hand_play)
        # hit
        self.hit(dealer, hand_play)

    @check_if_done_first
    def split(self, dealer: Dealer, hand_play: HandPlay) -> bool:
        if hand_play.can_split() and hand_play.player.strategy.split(
            dealer.hand, hand_play.hand
        ):
            hand_play.player.cash -= hand_play.betsize
            hand_index = self.hands.index(hand_play)
            self.hands.remove(hand_play)

            new_hands = HandPlay.split(
                hand_play.betsize, hand_play.player, hand_play.hand, hand_play.splits
            )
            for hand in new_hands:
                dealer.deal(hand.hand)
            self.hands[hand_index:hand_index] = self.hands
            return True
        return False

    @check_if_done_first
    def double(self, dealer: Dealer, hand_play: HandPlay) -> bool:
        if hand_play.player.strategy.double(dealer.hand, hand_play.hand):
            hand_play.player.cash -= hand_play.betsize
            hand_play.betsize *= 2
            dealer.deal(hand_play.hand)
            hand_play.done()
            return True
        return False

    @check_if_done_first
    def hit(self, dealer: Dealer, hand_play: HandPlay) -> bool:
        while (not hand_play.is_done) and (
            hand_play.player.strategy.hit(dealer.hand, hand_play.hand)
        ):
            dealer.deal(hand_play.hand)
        hand_play.done()
        return False

    def initial_deal(self):
        pass


@dataclass
class Round:
    dealer: Dealer
    table: Table

    def shuffle(self) -> Self:
        self.dealer.shuffle()
        return self

    def place_bets(self) -> Self:
        return self

    def deal(self) -> Self:
        self.table.initial_deal()
        return self

    def check_for_blackjack(self) -> Self:
        return self

    def insurance(self) -> Self:
        return self

    def check_for_21(self) -> Self:
        return self

    def player_play(self) -> Self:

        return self

    def dealer_play(self) -> Self:
        return self

    def eval_insurance(self) -> Self:
        return self

    def eval_hands(self) -> Self:
        return self

    def play(self) -> Self:
        return (
            self.shuffle()
            .place_bets()
            .deal()
            .check_for_blackjack()
            .insurance()
            .check_for_21()
            .player_play()
            .dealer_play()
            .eval_insurance()
            .eval_hands()
        )


def player_factory(number_of_players: int = 1) -> list[Player]:
    return [Player() for _ in range(number_of_players)]


@dataclass
class Game:
    dealer: Dealer = field(default_factory=Dealer)
    shoe: Shoe = field(default_factory=partial(Shoe, NUMBER_OF_DECKS))
    players: list[Player] = field(default_factory=player_factory)
    round: Round = field(init=False)

    def __post_init__(self):
        self.round = Round(self.shoe, self.dealer, self.players)

    def loop_play(self):
        while True:
            self.round = self.round.play()
