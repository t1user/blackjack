from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from functools import cached_property, partial, reduce, wraps
from operator import ior
from typing import Any, Callable, ClassVar, Self, TypeVar

# ### Rules ###
MAX_SPLITS = -1  # negative number means no limit
SINGLE_CARD_ON_SPLIT_ACES = True
BURN_PERCENT_RANGE = (20, 25)  # penetration percentage range (min, max)
NUMBER_OF_DECKS = 6
PLAYER_CASH = 1_000
BLACKJACK_PAYOUT = 3 / 2
TABLE_LIMITS = (5, 50)
SURRENDER = True  # No extra conditions DON'T CHANGE IT, NOT READY YET
DOUBLE_ON_SPLIT = True
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
            return 1
        else:
            return int(self.rank)

    @cached_property
    def soft_value(self):
        if not self.is_ace:
            return self.value
        else:
            return 11

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

    @property
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
        self._no_blackjack = False

    @classmethod
    def from_split(cls, *cards: Card) -> Self:
        hand = cls(*cards)
        hand._no_blackjack = True
        return hand

    @property
    def value(self) -> int:
        if (sv := self.soft_value) <= 21:
            return sv
        else:
            return self.hard_value

    @property
    def hard_value(self) -> int:
        return sum([card.value for card in self])

    @property
    def soft_value(self) -> int:
        if self._has_ace():
            return (
                11
                + (len([card for card in self if card.is_ace]) - 1)
                + sum([card.value for card in self if not card.is_ace])
            )
        else:
            return sum([card.value for card in self])

    def is_bust(self) -> bool:
        return self.value > 21

    def _has_face(self) -> bool:
        return any([card.is_face for card in self])

    def _has_ace(self) -> bool:
        return any([card.rank == "A" for card in self])

    def is_double_aces(self) -> bool:
        return all([card.is_ace for card in self])

    def is_blackjack(self) -> bool:
        if self._no_blackjack:
            return False
        else:
            return (len(self) == 2) and (self.value == 21)

    def can_split(self) -> bool:
        return (len(self) == 2) and (
            (self[0].rank == self[1].rank)
            or all([(card.rank in FACES) for card in self])
        )

    def value_str(self) -> str:
        if self.is_blackjack():
            return "BLACKJACK"
        elif self.is_bust():
            return "BUST"
        elif (
            (hv := self.hard_value) != (sv := self.soft_value)
        ) and self.soft_value <= 21:
            return f"{hv}/{sv}"
        else:
            return str(self.value)

    def dealer_value_str(self) -> str:
        if self.is_blackjack():
            return "BLACKJACK"
        else:
            return str(self.value)

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
        elif self.is_bust() and not other.is_bust():
            return False
        elif not self.is_bust() and other.is_bust():
            return True
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
        elif self.is_bust() and not other.is_bust():
            return True
        elif not self.is_bust() and other.is_bust():
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

    __repr__ = __str__


class GameStrategy(ABC):

    @abstractmethod
    def play(
        self, dealer_hand: Hand, player_hand: Hand, choices: PlayDecision
    ) -> PlayDecision: ...

    @abstractmethod
    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool: ...

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}()"


class BettingStrategy(ABC):

    @abstractmethod
    def bet(self, *args: Any, **kwargs: Any) -> float:
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}()"


class DealerStrategy:

    def play(self, dealer_hand: Hand, *args) -> PlayDecision:  # type: ignore
        return PlayDecision.HIT if dealer_hand.soft_value < 17 else PlayDecision.STAND

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}()"


@dataclass
class Dealer:
    shoe: Shoe = field(default_factory=partial(Shoe, NUMBER_OF_DECKS))
    hand: Hand = field(default_factory=Hand)
    strategy: DealerStrategy = DealerStrategy()

    def deal(self, hand: Hand | HandPlay) -> None:
        hand += self.shoe.pop()

    def deal_self(self) -> None:
        self.deal(self.hand)

    def shuffle(self) -> None:
        self.hand = Hand()
        if self.shoe.will_shuffle:
            self.shoe.shuffle()

    def force_shuffle(self) -> None:
        self.shoe.shuffle()

    @property
    def has_ace(self):
        if len(self.hand) != 1:
            raise GameError(
                f"Checking for dealer Ace, when dealer has {len(self.hand)} cards."
            )
        else:
            return self.hand[0].is_ace

    def __repr__(self) -> str:
        return f"Dealer(hand={str(self.hand)})"


@dataclass
class Player:
    strategy: GameStrategy
    betting_strategy: BettingStrategy
    cash: float = PLAYER_CASH
    number_of_hands: int = 1

    def charge(self, amount: float) -> float:
        if amount > self.cash:
            raise NotEnoughCash("Not enough cash")
        else:
            self.cash -= amount
            return self.cash

    def credit(self, amount: float) -> float:
        self.cash += amount
        return self.cash

    def bet(self) -> float:
        try:
            betsize = self.betting_strategy.bet()
        except NotEnoughCash:
            betsize = self.cash
        self.charge(betsize)
        return betsize


T = TypeVar("T")


class PlayDecision(Flag):
    HIT = auto()
    SPLIT = auto()
    DOUBLE = auto()
    STAND = auto()
    SURRENDER = auto()

    @classmethod
    def from_predicates(
        cls, predicates: tuple[bool, bool, bool, bool, bool]
    ) -> PlayDecision:
        return reduce(
            ior, [flag for flag, predicate in zip(cls, predicates) if predicate]
        )


@dataclass
class HandPlay:
    """
    Container for all information relevant to how a Hand is played and methods
    evaluating wheather play was won or lost.
    """

    player: Player
    betsize: float
    hand: Hand = field(default_factory=Hand)
    insurance: float = 0
    splits: int = 0
    _is_done: bool = field(default=False, repr=False)
    _winnings: float = field(default=0, repr=False)
    _losses: float = field(default=0, repr=False)

    def __post_init__(self):
        self._losses = -self.betsize

    @classmethod
    def from_player(cls, player: Player) -> Self | None:
        betsize = min(player.bet(), TABLE_LIMITS[1])
        if betsize >= TABLE_LIMITS[0]:
            return cls(player, betsize)
        else:
            player.cash += betsize
            raise NotEnoughCash

    @staticmethod
    def check_if_done_first(func: Callable[..., T]) -> Callable[..., T | bool]:
        """
        Decorator, will prevent calling a function when hand is already done.
        Can be applied to methods that don't accept arguments.
        """

        @wraps(func)
        def wrapper(self: HandPlay) -> T | bool:
            if self.is_done:
                return False
            else:
                return func(self)

        return wrapper

    def charge(self, amount: float) -> None:
        self.player.charge(amount)
        self._losses -= amount

    def credit(self, amount: float) -> None:
        self._winnings += amount

    def charge_bet(self, bet_multiple: float = 1) -> None:
        amount = self.betsize * bet_multiple
        self.charge(amount)

    def credit_bet(self, bet_multiple: float = 1) -> None:
        self.credit(self.betsize * bet_multiple)

    @property
    def allowed_choices(self) -> PlayDecision | None:
        if self.is_done:
            return
        else:
            predicates = (
                self.can_hit(),
                self.can_split(),
                self.can_double(),
                self.can_stand(),
                self.can_surrender(),
            )
            if any(predicates):
                return PlayDecision.from_predicates(predicates)

    @property
    def result(self) -> float:
        if self.is_done:
            return self._winnings + self._losses
        else:
            return 0

    @property
    def is_bust(self):
        return self.hand.is_bust()

    @property
    def is_done(self) -> bool:
        self._is_done = (
            # has manually been set to done
            self._is_done
            # is bust
            or self.is_bust
            # is blackjack
            or self.hand.is_blackjack()
            # is 21 (you may still want to hit soft 21)
            or self.hand.hard_value == 21
        )
        return self._is_done

    def done(self) -> None:
        self._is_done = True

    def surrender(self, dealer: Dealer) -> None:
        self.credit_bet(0.5)
        self.hand = Hand()
        self.done()

    def play_insurance(self, dealer: Dealer) -> None:
        if self.player.strategy.insurance(dealer.hand, self.hand):
            try:
                self.charge_bet(0.5)
                self.insurance = 0.5 * self.betsize
            except NotEnoughCash:
                pass

    def play(self, dealer: Dealer) -> list[Self] | Self | None:
        if self.allowed_choices is None:
            return None
        decision = self.player.strategy.play(
            dealer.hand, self.hand, self.allowed_choices
        )  # type: ignore
        try:
            assert decision in self.allowed_choices
        except AssertionError as e:
            raise GameError from e

        match decision:
            case PlayDecision.HIT:
                return self.hit(dealer)
            case PlayDecision.SPLIT:
                return self.split(dealer)
            case PlayDecision.DOUBLE:
                return self.double(dealer)
            case PlayDecision.STAND:
                return self.stand(dealer)
            case PlayDecision.SURRENDER:
                return self.surrender(dealer)
            case _:
                raise GameError("Unknown play decision")

    def double(self, dealer: Dealer) -> None:
        self.charge_bet(1)
        self.betsize *= 2
        dealer.deal(self)
        self.done()

    def split(self, dealer: Dealer) -> list[Self]:
        self.charge_bet()
        is_done = (
            True
            if (SINGLE_CARD_ON_SPLIT_ACES and self.hand.is_double_aces())
            else self._is_done
        )
        new_hands = self.__class__._split(
            self.betsize,
            self.player,
            self.hand,
            self.splits,
            self.insurance,
            _is_done=is_done,
        )
        for hand_play in new_hands:
            dealer.deal(hand_play)
        return new_hands

    def hit(self, dealer: Dealer) -> Self:
        dealer.deal(self)
        return self

    def stand(self, dealer: Dealer) -> None:
        self.done()

    def eval_hand(self, dealer: Dealer) -> None:
        dealer_hand = dealer.hand
        if self.hand > dealer_hand:
            if self.hand.is_blackjack():
                self.credit_bet(2.5)
            else:
                self.credit_bet(2)
        elif self.hand == dealer_hand:
            self.credit_bet(1)
        self.player.credit(self._winnings)

    def eval_insurance(self, dealer: Dealer) -> None:
        if not self.insurance:
            return
        dealer_hand = dealer.hand
        if dealer_hand.is_blackjack():
            self.credit(self.insurance * 3)

    def __iadd__(self, card: Card) -> Self:
        self.hand.append(card)
        return self

    def can_surrender(self) -> bool:
        # override to enter surrender conditions
        if not SURRENDER:
            return False
        if self.is_done:
            return False
        elif len(self.hand) > 2:
            return False
        else:
            return True

    def can_double(self) -> bool:
        if self.is_done:
            return False
        elif self.player.cash < self.betsize:
            return False
        elif (not DOUBLE_ON_SPLIT) and self.splits:
            return False
        else:
            return len(self.hand) == 2

    def can_split(self) -> bool:
        if self.is_done:
            return False
        elif self.player.cash < self.betsize:
            return False
        elif (MAX_SPLITS > 0) and (self.splits > MAX_SPLITS):
            return False
        else:
            return self.hand.can_split()

    def can_hit(self) -> bool:
        return not self.is_done

    def can_stand(self) -> bool:
        return not self.is_done

    @classmethod
    def _split(
        cls,
        bet_size: float,
        player: Player,
        hand: Hand,
        splits: int,
        insurance: float,
        **kwargs: Any,
    ) -> list[Self]:
        new_hands = [
            cls(player, bet_size, Hand.from_split(card), splits=splits + 1, **kwargs)
            for card in reversed(hand)
        ]
        new_hands[0].insurance = insurance
        return new_hands

    def __str__(self) -> str:
        return str(self.hand)


@dataclass
class TablePlay:
    _hands: list[HandPlay] = field(default_factory=list, repr=False)
    _done: list[HandPlay] = field(default_factory=list, init=False, repr=False)
    _methods: ClassVar = (
        "play_insurance",
        "play",
        "eval_hand",
        "eval_insurance",
    )

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> HandPlay:
        try:
            return self._hands.pop()
        except IndexError:
            self._hands = self._done
            self._done = []
            raise StopIteration

    def __getattr__(self, name: str):
        if name in self._methods:
            return partial(self.run_all_hands, name)
        else:
            raise AttributeError

    def run_all_hands(self, name: str, dealer: Dealer):
        for hand_play in self:
            method = getattr(hand_play, name)
            hand_hands_or_none = method(dealer)
            if hasattr(hand_hands_or_none, "__iter__"):
                self._hands.extend(hand_hands_or_none)
            elif hand_hands_or_none is None:
                self._done.append(hand_play)
            else:
                try:
                    assert isinstance(hand_hands_or_none, HandPlay)
                except AssertionError as e:
                    raise GameError(
                        f"Wrong hand received from play: {hand_hands_or_none}"
                    ) from e
                self._hands.append(hand_hands_or_none)

    @property
    def hands(self):
        return [*self._hands, *self._done]

    def deal_card(self, dealer: Dealer):
        for hand in self.hands:
            dealer.deal(hand)

    def __repr__(self) -> str:
        return f"TablePlay(hands={self.hands})"


@dataclass
class Round:
    dealer: Dealer
    table: TablePlay

    def shuffle(self) -> Self:
        self.dealer.shuffle()
        return self

    def deal(self) -> Self:
        self.table.deal_card(self.dealer)
        self.dealer.deal_self()
        self.table.deal_card(self.dealer)
        return self

    def offer_insurance(self) -> Self:
        if self.dealer.has_ace:
            self.table.play_insurance(self.dealer)
        return self

    def player_play(self) -> Self:
        self.table.play(self.dealer)
        return self

    def dealer_play(self) -> Self:
        # dealer takes card if there is at least one non-busted hand
        # surrendered hand (value == 0) shouldn't be a reason to take card
        # or insurance in play:
        if any(
            [not hand.is_bust for hand in self.table.hands if hand.hand.value != 0]
        ) or any([hand.insurance for hand in self.table.hands]):
            while (
                self.dealer.strategy.play(self.dealer.hand)  # type: ignore
                is PlayDecision.HIT
            ):
                self.dealer.deal_self()
        return self

    def eval_insurance(self) -> Self:
        self.table.eval_insurance(self.dealer)
        return self

    def eval_hands(self) -> Self:
        self.table.eval_hand(self.dealer)
        return self

    def play(self) -> Self:
        return (
            self.shuffle()
            .deal()
            .offer_insurance()
            .player_play()
            .dealer_play()
            .eval_insurance()
            .eval_hands()
        )


class NotEnoughCash(Exception):
    pass


class GameError(Exception):
    pass


@dataclass
class Game:
    """
    Main game loop.

    Subclass `Game` to add any interface specific features.

    Parameters:

    players: list of player objects


    """

    players: list[Player]
    dealer: Dealer = field(default_factory=Dealer)

    def round(self):
        hand_plays: list[HandPlay] = []
        for player in self.players:
            for _ in range(player.number_of_hands):
                hand_play = HandPlay.from_player(player)
                if hand_play is not None:
                    hand_plays.append(hand_play)
        return Round(self.dealer, TablePlay(hand_plays))

    def play(self) -> Round:
        return self.round().play()

    def loop_play(self):
        while True:
            self.play()
