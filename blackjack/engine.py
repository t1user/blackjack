from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from functools import cached_property, partial, reduce, wraps
from operator import ior
from typing import (
    Any,
    Callable,
    ClassVar,
    Generator,
    Iterable,
    Literal,
    NamedTuple,
    Self,
    TypeVar,
)

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

    @cached_property
    def hilo_count(self):
        if self.is_ace or self.value == 10:
            return -1
        elif self.value <= 6:
            return 1
        else:
            return 0

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
        self.hilo_count = 0
        self.shuffle()

    @property
    def will_shuffle(self) -> bool:
        if len(self) < self._cut_card:
            return True
        else:
            return False

    def shuffle(self) -> None:
        self.clear()
        self.hilo_count = 0
        self.extend([*DECK * self.decks])
        random.shuffle(self)
        self._cut_card = int(random.randint(*BURN_PERCENT_RANGE) * len(self) / 100)

    def deal(self) -> Card:
        card = self.pop()
        self.hilo_count += card.hilo_count
        return card

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
        if len(self) < 2:
            return ""
        if self.is_blackjack():
            return "BJ"
        elif self.is_bust():
            return "BUST"
        elif (
            (hv := self.hard_value) != (sv := self.soft_value)
        ) and self.soft_value <= 21:
            return f"{hv}/{sv}"
        else:
            return str(self.value)

    def dealer_value_str(self) -> str:
        if len(self) < 2:
            return ""
        elif self.is_blackjack():
            return "BJ"
        elif self.is_bust():
            return "BUST"
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
        return PlayDecision.HIT if dealer_hand.value < 17 else PlayDecision.STAND

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
    strategy: GameStrategy | None
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


class State(Enum):
    DONE = auto()
    NOT_DONE = auto()


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
    _is_cashed: bool = field(default=False, repr=True)

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
        Decorator, will prevent calling a method when hand is already done.
        """

        @wraps(func)
        def wrapper(self: HandPlay, *args: Any, **kwargs: Any) -> T | bool:
            if self.is_done:
                return False
            else:
                return func(self, *args, **kwargs)

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
        if self._is_cashed:
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

    def surrender(self, dealer: Dealer) -> State:
        self.credit_bet(0.5)
        self.hand = Hand()
        self.done()
        self.cash_out(dealer)
        return State.DONE

    def play_insurance(self, dealer: Dealer) -> State | Callable[[bool], State]:
        if self.player.cash < 0.5 * self.betsize:
            return State.DONE

        if self.player.strategy is None:
            return self.process_insurance_decision
        else:
            return self.process_insurance_decision(
                self.player.strategy.insurance(dealer.hand, self.hand)
            )

    def process_insurance_decision(self, decision: bool) -> State:
        if decision:
            self.charge_bet(0.5)
            self.insurance = 0.5 * self.betsize
        return State.DONE

    def play(
        self, dealer: Dealer
    ) -> (
        list[Self] | Self | State | Callable[[PlayDecision], list[Self] | Self | State]
    ):
        if self.allowed_choices is None:
            return State.DONE
        if self.player.strategy is None:
            return partial(self.process_decision, dealer)
        else:
            return self.process_decision(
                dealer,
                self.player.strategy.play(dealer.hand, self.hand, self.allowed_choices),
            )

    def process_decision(
        self, dealer: Dealer, decision: PlayDecision
    ) -> list[Self] | Self | State:
        try:
            assert self.allowed_choices is not None
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

    def double(self, dealer: Dealer) -> State:
        self.charge_bet(1)
        self.betsize *= 2
        dealer.deal(self)
        self.done()
        return State.DONE

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

    def stand(self, dealer: Dealer) -> State:
        self.done()
        return State.DONE

    def eval_insurance(self, dealer: Dealer) -> State:
        if self.insurance and dealer.hand.is_blackjack():
            self.credit(self.insurance * 3)
        return State.DONE

    def eval_hand(self, dealer: Dealer) -> State:
        dealer_hand = dealer.hand
        if self.hand > dealer_hand:
            if self.hand.is_blackjack():
                self.credit_bet(2.5)
            else:
                self.credit_bet(2)
        elif self.hand == dealer_hand:
            self.credit_bet(1)
        return State.DONE

    def cash_out(self, _) -> State:
        if not self._is_cashed:
            self.player.credit(self._winnings)
            self._is_cashed = True
        return State.DONE

    def __iadd__(self, card: Card) -> Self:
        self.hand.append(card)
        return self

    @check_if_done_first
    def can_surrender(self) -> bool:
        # override to enter surrender conditions
        if not SURRENDER:
            return False
        elif len(self.hand) > 2 or self.splits:
            return False
        else:
            return True

    @check_if_done_first
    def can_double(self) -> bool:
        if self.player.cash < self.betsize:
            return False
        elif (not DOUBLE_ON_SPLIT) and self.splits:
            return False
        else:
            return len(self.hand) == 2

    @check_if_done_first
    def can_split(self) -> bool:
        if self.player.cash < self.betsize:
            return False
        elif (MAX_SPLITS > 0) and (self.splits > MAX_SPLITS):
            return False
        else:
            return self.hand.can_split()

    @check_if_done_first
    def can_hit(self) -> bool:
        return True

    @check_if_done_first
    def can_stand(self) -> bool:
        return True

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
    _done: list[HandPlay] = field(default_factory=list, repr=False)
    _in_progress: HandPlay | None = field(default=None, repr=False)
    _methods: ClassVar = (
        "play_insurance",
        "play",
        "eval_hand",
        "eval_insurance",
        "cash_out",
    )
    choices: PlayDecision | None = None

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> HandPlay:
        try:
            self._in_progress = self._hands.pop()
            return self._in_progress
        except IndexError:
            self._hands = list(reversed(self._done))
            self._done = []
            raise StopIteration

    def __getattr__(self, name: str):
        if name in self._methods:
            return partial(self.run_all_hands, name)
        else:
            raise AttributeError

    def run_all_hands(self, name: str, dealer: Dealer) -> Generator[None | Callable]:
        # This is a generator that yields a callable if it needs a decision
        # and raises StopIteration otherwise
        # Hand that returns State.DONE is done, otherwise it needs further processing
        for hand_play in self:
            method = getattr(hand_play, name)
            hand_hands_or_none = method(dealer)

            if callable(hand_hands_or_none):
                self.choices = hand_play.allowed_choices
                feedback = yield hand_hands_or_none
                if feedback is not None:
                    hand_hands_or_none = feedback

            if hand_hands_or_none is State.DONE:
                self._done.append(hand_play)
            elif hasattr(hand_hands_or_none, "__iter__"):
                assert not callable(hand_hands_or_none)
                self._hands.extend(hand_hands_or_none)
            else:
                try:
                    assert isinstance(hand_hands_or_none, HandPlay)
                except AssertionError as e:
                    raise GameError(
                        f"Wrong hand received from play: {hand_hands_or_none}"
                    ) from e
                self._hands.append(hand_hands_or_none)
            self._in_progress = None

    @property
    def hands(self):
        if self._in_progress is None:
            return [*self._hands, *self._done]
        else:
            return [*self._hands, self._in_progress, *reversed(self._done)]

    def deal_card(self, dealer: Dealer):
        for hand in self.hands:
            dealer.deal(hand)

    def __repr__(self) -> str:
        return f"TablePlay(hands={self.hands})"


@dataclass
class DecisionCallable:
    callable: Callable

    def __call__(self, decision):
        return self.callable(decision)


class InsuranceDecisionCallable(DecisionCallable):
    pass


class PlayDecisionCallable(DecisionCallable):
    pass


class DecisionTuple(NamedTuple):
    callable: Callable
    options: Iterable


class DecisionHandler:

    def __init__(
        self,
        gen: Generator,
        next_step: Callable,
        decision_tuple: DecisionTuple,
    ):
        self.gen = gen
        self.next_step = next_step
        self.decision_function, self.choices = decision_tuple
        self.decision_callable = None

        self.make_callable()

    @classmethod
    def from_gen(cls, gen: Generator, next_step: Callable) -> Self | None:
        try:
            decision_tuple = next(gen)
        except StopIteration:
            return
        else:
            return cls(gen, next_step, decision_tuple)

    def __call__(self, decision):
        assert self.decision_callable is not None
        self.decision_callable(decision)

    def make_callable(self):

        def inner(decision: PlayDecision | bool):
            self.decision_callable = None
            self.choices = None
            try:
                next_decision_tuple = self.gen.send(self.decision_function(decision))
            except StopIteration:
                self.next_step()
            else:
                self.decision_function, self.choices = next_decision_tuple
                self.make_callable()

        self.decision_callable = inner

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.gen})"


@dataclass
class Round:
    dealer: Dealer
    table: TablePlay
    decision_callable: DecisionCallable | None = None

    @property
    def choices(self) -> PlayDecision:
        try:
            assert self.table.choices
        except AssertionError as e:
            raise GameError("Accessing choices when none are available") from e
        return self.table.choices

    def process_decision(
        self,
        gen: Generator,
        next_function: Callable,
        decision_type: Literal["play", "insurance"] = "play",
    ) -> Self | None:

        try:
            decision_function = next(gen)
        except StopIteration:
            return next_function()
        else:
            self.make_callable(gen, next_function, decision_function, decision_type)

    def make_callable(
        self,
        gen: Generator,
        next_function: Callable,
        decision_function: Callable,
        decision_type: Literal["play", "insurance"],
    ):

        def inner(decision: PlayDecision | bool):
            self.decision_callable = None
            try:
                next_decision_function = gen.send(decision_function(decision))
            except StopIteration:
                next_function()
            else:
                self.make_callable(
                    gen, next_function, next_decision_function, decision_type
                )

        decision_class = {
            "play": PlayDecisionCallable,
            "insurance": InsuranceDecisionCallable,
        }.get(decision_type)

        if decision_class:
            self.decision_callable = decision_class(inner)

    def shuffle(self) -> Self | None:
        self.dealer.shuffle()
        return self.deal()

    def deal(self) -> Self | None:
        self.table.deal_card(self.dealer)
        self.dealer.deal_self()
        self.table.deal_card(self.dealer)
        return self.offer_insurance()

    def offer_insurance(self) -> Self | None:
        if self.dealer.has_ace:
            insurance_result = self.table.play_insurance(self.dealer)
            return self.process_decision(
                insurance_result, self.player_play, "insurance"
            )
        return self.player_play()

    def player_play(self) -> Self | None:
        play_results = self.table.play(self.dealer)
        return self.process_decision(play_results, self.dealer_play)

    def dealer_play(self) -> Self | None:
        # dealer takes card if there is at least one non-busted hand
        # surrendered hand (value == 0) shouldn't be a reason to take card
        # or insurance in play:
        if any(
            [
                self._is_reason(self.dealer.hand, player_hand)
                for player_hand in self.table.hands
            ]
        ) or any([hand.insurance for hand in self.table.hands]):
            while (
                self.dealer.strategy.play(self.dealer.hand)  # type: ignore
                is PlayDecision.HIT
            ):
                self.dealer.deal_self()
        return self.eval_insurance()

    def eval_insurance(self) -> Self | None:
        evi = self.table.eval_insurance(self.dealer)
        return self.process_decision(evi, self.eval_hands)

    def eval_hands(self) -> Self | None:
        ev = self.table.eval_hand(self.dealer)
        return self.process_decision(ev, self.cash_out)

    def cash_out(self) -> Self | None:
        co = self.table.cash_out(self.dealer)
        return self.process_decision(co, lambda: self)

    @staticmethod
    def _is_reason(dealer_hand: Hand, player_hand: HandPlay) -> bool:
        """
        Check if player_hand should be a reason for the dealer to draw card.
        False means that the outcome of this hand is already determined.
        """
        if player_hand.is_bust:
            return False
        elif player_hand.hand.value == 0:  # surrendered hand
            return False
        elif player_hand.hand.is_blackjack and not (
            dealer_hand._has_ace or dealer_hand._has_face
        ):
            return False
        elif player_hand.hand.is_blackjack and len(dealer_hand) > 1:
            return False
        else:
            return True

    @property
    def pipe(self) -> list[Callable]:
        return [
            self.shuffle,
            self.deal,
            self.offer_insurance,
            self.player_play,
            self.dealer_play,
            self.eval_insurance,
            self.eval_hands,
            self.cash_out,
        ]

    @staticmethod
    def step(func):
        def wrapper(self) -> Self | None:
            try:
                next_step = next(self._step)
            except StopIteration:
                return self

            if (gen := func()) is None:
                return next_step()
            else:
                if decision_callable := DecisionHandler.from_gen(gen, next_step):
                    self.decision_callable = decision_callable
                else:
                    return next_step()

        return wrapper

    def steps(self):
        for i in self.pipe:
            yield i

    def _play(self) -> Self | None:
        self._step = self.steps()
        try:
            first_step = next(self._step)
        except StopIteration:
            return self
        return first_step()

    def play(self) -> Self | None:
        return self.shuffle()


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
    round: Round = field(init=False)

    def __post_init__(self):
        self.round = Round(self.dealer, TablePlay())

    def make_round(self):
        hand_plays: list[HandPlay] = []
        for player in self.players:
            for _ in range(player.number_of_hands):
                hand_play = HandPlay.from_player(player)
                if hand_play is not None:
                    hand_plays.append(hand_play)
        return Round(self.dealer, TablePlay(hand_plays))

    def play(self) -> Round | None:
        self.round = self.make_round()
        return self.round.play()

    def loop_play(self):
        while True:
            self.play()
