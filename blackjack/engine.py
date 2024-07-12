import random
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property, partial
from typing import Self

from .strategies import GameStrategy

# ### Rules ###
MAX_SPLITS = -1  # negative number means no limit
RESPLIT_ACES = False
BURN_PERCENT_RANGE = (20, 25)  # penetration percentage range (min, max)
NUMBER_OF_DECKS = 6
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

    def __init__(self, *cards: Card, splits: int = 0) -> None:
        super().__init__(cards)
        self._splits = 0

    @property
    def value(self) -> int:
        if (v := max(self.hard_value, self.soft_value)) <= 21:
            return v
        else:
            return self.soft_value

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

    def is_blackjack(self) -> bool:
        return (len(self) == 2) and self._has_face() and self._has_ace()

    def can_split(self) -> bool:
        if self._splits > MAX_SPLITS:
            return False
        else:
            return (len(self) == 2) and (
                (self[0].rank == self[1].rank)
                or all([(card.rank in FACES) for card in self])
            )

    def value_str(self) -> str:
        if self.hard_value != self.soft_value:
            return f"{self.soft_value}/{self.hard_value}"
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

    @classmethod
    def split(cls, hand: Self) -> list[Self]:
        return [
            cls(hand[0], splits=hand._splits + 1),
            cls(hand[1], splits=hand._splits + 1),
        ]


@dataclass
class HandPlay:
    hand: Hand
    bet: int
    insurance: bool = False
    splits: int = 0


class BettingStrategy:
    pass


class Player:
    cash: int
    game_strategy: GameStrategy
    betting_strategy: BettingStrategy
    hands: list[Hand]


class Dealer(Player):
    pass


class PlayerList(list[Player]):
    def __init__(self, *players: Player) -> None:
        super().__init__(players)

    def _chain(
        self, attr1: str, attr2: str, dealer_hand: Hand, player_hand: Hand
    ) -> None:
        for player in self:
            player_method = getattr(player, attr1)
            strategy_method = getattr(player_method, attr2)
            strategy_method(dealer_hand, player_hand)

    def play(self, action: str, dealer_hand: Hand, player_hand: Hand) -> None:
        self._chain("game_strategy", action, dealer_hand, player_hand)

    def bet(self, action: str, dealer_hand: Hand, player_hand: Hand) -> None:
        self._chain("betting_strategy", action, dealer_hand, player_hand)

    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> None:
        self.play("insurance", dealer_hand, player_hand)

    def split(self, dealer_hand: Hand, player_hand: Hand) -> None:
        self.play("split", dealer_hand, player_hand)

    def double(self, dealer_hand: Hand, player_hand: Hand) -> None:
        self.play("double", dealer_hand, player_hand)

    def hit(self, dealer_hand: Hand, player_hand: Hand) -> None:
        self.play("hit", dealer_hand, player_hand)


@dataclass
class Round:
    shoe: Shoe
    dealer: Dealer
    players: list[Player] = field(default_factory=list)

    def shuffle(self) -> Self:
        if self.shoe.will_shuffle():
            self.shoe.shuffle()
        return self

    def place_bets(self) -> Self:
        return self

    def deal(self) -> Self:
        return self

    def check_for_blackjack(self) -> Self:
        return self

    def insurance(self) -> Self:
        return self

    def check_for_21(self) -> Self:
        return self

    def player_play(self) -> Self:
        # split
        # double
        # hit
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

    def play(self):
        while True:
            self.round = self.round.play()
