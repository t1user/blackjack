from functools import wraps
from typing import Any, Callable, Literal

from blackjack.engine import Game, Hand, Player
from blackjack.strategies import BettingStrategy, GameStrategy

Decision = Literal["S", "P", "D", "H"]


class TextGameStrategy(GameStrategy):

    _allowed_choices: tuple[Decision, Decision, Decision, Decision] = (
        "P",
        "S",
        "D",
        "H",
    )
    _decision: str | None = None

    @staticmethod
    def print_hands(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(
            self: "TextGameStrategy",
            dealer_hand: Hand,
            player_hand: Hand,
            *args: Any,
            **kwargs: Any,
        ) -> Callable[..., Any]:
            print(f"Dealer hand: {str(dealer_hand)}, Your hand: {str(player_hand)}")
            return func(self, dealer_hand, player_hand, *args, **kwargs)

        return wrapper

    @staticmethod
    def asker(field: str) -> bool:
        o = None
        while o not in ("Y", "N"):
            o = (
                input(f"{field.upper()} (Y/N)? [Enter] for No --> ").upper().strip()
                or "N"
            )

        return True if o == "Y" else False

    @print_hands
    def surrender(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return self.asker("surrender")

    @print_hands
    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return self.asker("insurance")

    def split(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return self.stand_split_double_hit(dealer_hand, player_hand, "P")

    def double(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return self.stand_split_double_hit(dealer_hand, player_hand, "D")

    def hit(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return self.stand_split_double_hit(dealer_hand, player_hand, "H")

    @print_hands
    def stand_split_double_hit(
        self, dealer_hand: Hand, player_hand: Hand, action: Decision
    ) -> bool:
        d = self._decision or self.play()
        if d == action:
            self._decision = None
            return True
        else:
            return False

    def play(self) -> Decision:
        while self._decision not in self._allowed_choices:
            self._decision = input("(S)tand / s(P)lit / (D)ouble, (H)it --> ").upper()
        return self._decision


class TextBettingStrategy(BettingStrategy):

    def __init__(self, betsize: float) -> None:
        self.betsize = betsize

    def bet(self, *args: Any, **kwargs: Any):
        while True:
            i = (
                input(f"Input bet size or [Enter] for: {self.betsize} -> ")
                .upper()
                .strip()
                or self.betsize
            )
            try:
                return float(i)
            except ValueError:
                print(f"wrong value: {i}, try again...")


if __name__ == "__main__":
    game = Game([Player(TextGameStrategy(), TextBettingStrategy(5))])
    game.play()
