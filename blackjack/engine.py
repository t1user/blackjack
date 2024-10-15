from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property, partial, wraps
from typing import Any, Callable, ClassVar, Literal, Self, TypeVar

from .strategies import (
    BettingStrategy,
    DealerStrategy,
    FixedBettingStrategy,
    GameStrategy,
    RandomStrategy,
)

# ### Rules ###
MAX_SPLITS = -1  # negative number means no limit
RESPLIT_ACES = False
BURN_PERCENT_RANGE = (20, 25)  # penetration percentage range (min, max)
NUMBER_OF_DECKS = 6
PLAYER_CASH = 1_000
BLACKJACK_PAYOUT = 3 / 2
TABLE_LIMITS = (5, 50)
SURRENDER = True  # No extra conditions
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

    __repr__ = __str__


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


@dataclass
class HandPlay:
    """
    Container for all information relevant to how a Hand is played and methods
    evaluating wheather play was won or lost.
    """

    player: Player
    betsize: float
    hand: Hand = field(default_factory=Hand)
    insurance: bool = False
    splits: int = 0
    _is_done: bool = field(default=False, repr=False)
    _winnings: float = field(default=0, repr=False)
    _losses: float = field(default=0, repr=False)

    def __post_init__(self):
        self._losses = -self.betsize

    @classmethod
    def from_player(cls, player: Player) -> Self | None:
        betsize = player.bet()
        if TABLE_LIMITS[0] <= betsize <= TABLE_LIMITS[1]:
            return cls(player, betsize)
        else:
            player.cash += betsize

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

    def charge_bet(self, bet_multiple: float = 1) -> None:
        bet = self.betsize * bet_multiple
        self.player.charge(bet)
        self._losses -= bet

    def credit_bet(self, bet_multiple: float = 1) -> None:
        self._winnings += self.betsize * bet_multiple

    @property
    def allowed_choices(self) -> tuple[bool, bool, bool, bool]:
        return (self.can_stand(), self.can_split(), self.can_double(), self.can_hit())

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
            # no resplits on double aces if not allowed
            or (bool(self.splits) and RESPLIT_ACES and self.hand.is_double_aces())
            # is blackjack
            or self.hand.is_blackjack()
            # is 21
            or self.hand.value == 21
        )
        return self._is_done

    def done(self) -> None:
        self._is_done = True

    def surrender(self, dealer: Dealer) -> None:
        if self.can_surrender() and self.player.strategy.surrender(
            dealer.hand, self.hand
        ):
            self.credit_bet(0.5)
            self.done()

    def play_insurance(self, dealer: Dealer) -> None:
        if self.player.strategy.insurance(dealer.hand, self.hand):
            try:
                self.charge_bet()
                self.insurance = True
            except NotEnoughCash:
                pass

    def play(self, dealer: Dealer) -> list[Self] | Self | None:
        return self.split(dealer) or self.double(dealer) or self.hit(dealer)

    def double(self, dealer: Dealer) -> Self | None:
        if self.can_double() and self.player.strategy.double(dealer.hand, self.hand):
            try:
                self.charge_bet(1)
                dealer.deal(self)
                self.done()
                return self
            except NotEnoughCash:
                pass

    def split(self, dealer: Dealer) -> list[Self] | None:
        if self.can_split() and self.player.strategy.split(dealer.hand, self.hand):
            try:
                self.charge_bet()
                new_hands = self.__class__._split(
                    self.betsize, self.player, self.hand, self.splits
                )
                for hand_play in new_hands:
                    dealer.deal(hand_play)
                return new_hands
            except NotEnoughCash:
                pass

    def hit(self, dealer: Dealer) -> Self:
        while (not self.is_done) and (self.player.strategy.hit(dealer.hand, self.hand)):
            dealer.deal(self)
        self.done()
        return self

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
        dealer_hand = dealer.hand
        if dealer_hand.is_blackjack():
            if self.hand.is_blackjack():
                self.credit_bet(2.5)
            else:
                self.credit_bet(1.5)

    def __iadd__(self, card: Card) -> Self:
        self.hand.append(card)
        return self

    def can_surrender(self) -> bool:
        # override to enter surrender conditions
        if self.is_done:
            return False
        else:
            return True

    def can_double(self) -> bool:
        if self.is_done:
            return False
        elif (not DOUBLE_ON_SPLIT) and self.splits:
            return False
        else:
            return True

    def can_split(self) -> bool:
        if self.is_done:
            return False
        elif self.splits > MAX_SPLITS:
            return False
        else:
            return self.hand.can_split()

    def can_hit(self) -> bool:
        return not self.is_done

    def can_stand(self) -> bool:
        return True

    @classmethod
    def _split(
        cls, bet_size: float, player: Player, hand: Hand, splits: int, **kwargs: Any
    ) -> list[Self]:
        return [
            cls(player, bet_size, Hand(card), splits=splits + 1, **kwargs)
            for card in hand
        ]


@dataclass
class TablePlay:
    _hands: list[HandPlay] = field(default_factory=list, repr=False)
    _done: list[HandPlay] = field(default_factory=list, init=False, repr=False)
    _methods: ClassVar = (
        "surrender",
        "play_insurance",
        "double",
        "split",
        "hit",
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
            print(f"table reset")
            raise StopIteration

    def __getattr__(self, name: str):
        if name in self._methods:
            return partial(self.run_all_hands, name)
        else:
            raise AttributeError

    def run_all_hands(self, name: str, dealer: Dealer):
        for hand_play in self:
            method = getattr(hand_play, name)
            hands_or_hand = method(dealer)
            if hasattr(hands_or_hand, "__iter__"):
                self._hands.extend(hands_or_hand)
            else:
                self._done.append(hand_play)

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

    def offer_surrender(self) -> Self:
        if SURRENDER:
            self.table.surrender(self.dealer)
        return self

    def offer_insurance(self) -> Self:
        if self.dealer.has_ace:
            self.table.play_insurance(self.dealer)
        return self

    def split(self) -> Self:
        self.table.split(self.dealer)
        return self

    def double(self) -> Self:
        self.table.double(self.dealer)
        return self

    def hit(self) -> Self:
        self.table.hit(self.dealer)
        return self

    def player_play(self) -> Self:
        self.table.play(self.dealer)
        return self

    def dealer_play(self) -> Self:
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
            .offer_surrender()
            .offer_insurance()
            .split()
            .double()
            .hit()
            .dealer_play()
            .eval_insurance()
            .eval_hands()
        )


class NotEnoughCash(Exception):
    pass


class GameError(Exception):
    pass


def player_factory(number_of_players: int = 1) -> list[Player]:
    return [
        Player(RandomStrategy(), FixedBettingStrategy(5))
        for _ in range(number_of_players)
    ]


@dataclass
class Game:
    """
    Main game loop.

    Subclass `Game` to add any interface specific features.

    Parameters:

    players: list of player objects


    """

    players: list[Player] = field(default_factory=player_factory)
    dealer: Dealer = field(default_factory=Dealer)

    @property
    def round(self):
        hand_plays: list[HandPlay] = []
        for player in self.players:
            for _ in range(player.number_of_hands):
                hand_play = HandPlay.from_player(player)
                if hand_play is not None:
                    hand_plays.append(hand_play)
        return Round(self.dealer, TablePlay(hand_plays))

    def play(self):
        self.round.play()

    def loop_play(self):
        while True:
            self.play()
