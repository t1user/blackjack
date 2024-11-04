import sys
from functools import wraps
from typing import Any, Callable, ClassVar, Literal

from blackjack.engine import (
    TABLE_LIMITS,
    Game,
    Hand,
    NotEnoughCash,
    PlayDecision,
    Player,
    Round,
)
from blackjack.strategies import BettingStrategy, GameStrategy

DecisionMenmonics = Literal["H", "P", "D", "S", "R"]
DecisionString = Literal["HIT", "SPLIT", "DOUBLE", "STAND", "SURRENDER"]


class TextGameError(Exception):
    pass


class DecisionTranslator:
    _str_decision: ClassVar[dict[DecisionMenmonics, DecisionString]] = {
        "H": "HIT",
        "P": "SPLIT",
        "D": "DOUBLE",
        "S": "STAND",
        "R": "SURRENDER",
    }
    _decision_str: ClassVar[dict[DecisionString, DecisionMenmonics]] = {
        v: k for k, v in _str_decision.items()
    }

    _full_strings = {
        "H": "(H)it",
        "P": "S(P)lit",
        "D": "(D)ouble",
        "S": "(S)tand",
        "R": "Su(R)render",
    }

    def __init__(self, choices: PlayDecision):
        self.choices = choices

    def str_choices(self) -> list[DecisionMenmonics]:
        return [self._decision_str[c.name] for c in self.choices]  # type: ignore

    def full_choices_str(self) -> str:
        return ", ".join([self._full_strings[c] for c in self.str_choices()])

    def str_decision(self, s: DecisionMenmonics) -> PlayDecision:
        decision = self._str_decision.get(s)
        if decision is None:
            raise TextGameError("Wrong decision value")
        else:
            return PlayDecision[decision]


class TextGameStrategy(GameStrategy):

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
            print(
                f"Dealer hand: {str(dealer_hand)} ({dealer_hand.dealer_value_str()}), "
                f"Your hand: {str(player_hand)} ({player_hand.value_str()})"
            )
            return func(self, dealer_hand, player_hand, *args, **kwargs)

        return wrapper

    @staticmethod
    def asker(field: str) -> bool:
        o = None
        while o not in ("Y", "N"):
            o = (
                input(f"{field.upper()} (Y/N)? [Enter] for N --> ").upper().strip()
                or "N"
            )

        return True if o == "Y" else False

    @print_hands
    def play(
        self, dealer_hand: Hand, player_hand: Hand, choices: PlayDecision
    ) -> PlayDecision:
        translator = DecisionTranslator(choices)
        while (
            decision := input(
                f"{translator.full_choices_str()} or [Enter] for Stand --> "
            )
            .upper()
            .strip()
            or "S"
        ) not in translator.str_choices():
            pass
        return translator.str_decision(decision)

    @print_hands
    def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool:
        return self.asker("insurance")


class TextBettingStrategy(BettingStrategy):

    def __init__(self, betsize: float) -> None:
        self.betsize = betsize

    def bet(self, *args: Any, **kwargs: Any):
        while True:
            i = (
                input(
                    f'"Q" to quit; Enter BET ({TABLE_LIMITS[0]}-{TABLE_LIMITS[1]})'
                    f" or [Enter] for: {self.betsize} -> "
                )
                .upper()
                .strip()
                or self.betsize
            )
            if i == "Q":
                sys.exit()
            try:
                i = float(i)
            except ValueError:
                print(f"{i} is not a number, try again...")
                continue

            self.betsize = max(min(float(i), TABLE_LIMITS[1]), TABLE_LIMITS[0])
            print(f"BET: {self.betsize}")
            return self.betsize


class TextGame(Game):
    def play(self) -> Round:
        print("-----------------------------------")
        print(f"Your cash: {self.players[0].cash}")
        try:
            super().play()
        except NotEnoughCash:
            print("You don't have enought cash, you dumb fuck!")
            sys.exit()
        round = self.round
        print(">>>> ", end=" ")
        print(f"Dealer: {self.result_string(self.dealer.hand)} ")
        print(">>>> ", end=" ")
        print("Table: ", end=" ")
        assert round is not None
        for hp in round.table.hands:
            print(self.result_string(hp.hand), end=" ")
            print(self.translate_result(hp.result), end=" ")
            print(f"--> {'+' if hp.result > 0 else ''}{hp.result} |", end=" ")
        print()
        return round

    def result_string(self, hand: Hand) -> str:
        return f"{str(hand)} ({self.value_string(hand)})"

    def value_string(self, hand: Hand) -> str | float:
        if hand.is_bust():
            return "BUST"
        elif hand.is_blackjack():
            return "BLACKJACK"
        else:
            return hand.value

    def translate_result(self, result: float) -> str:
        if result > 0:
            return "WIN"
        elif result < 0:
            return "LOSS"
        else:
            return "PUSH"


if __name__ == "__main__":
    game = TextGame([Player(TextGameStrategy(), TextBettingStrategy(5))])
    print("---> W E L C O M E  T O  B L A C K J A C K <---")
    game.loop_play()
