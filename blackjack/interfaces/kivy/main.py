from typing import Any, Callable

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.slider import Slider

from blackjack import engine
from blackjack.engine import (
    Game,
    Hand,
    InsuranceDecisionCallable,
    PlayDecision,
    PlayDecisionCallable,
    Player,
)


class PlayDecisionButton(Button):
    action = ObjectProperty()

    def __init__(self, action: PlayDecision, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self.text = action.name

    def on_release(self, **kwargs):
        super().on_release(**kwargs)
        print(f"button pressed {self.text}")
        self.parent.decision = self.action


class DecisionButtons(BoxLayout):
    decision = ObjectProperty(None, allownone=True)

    def __init__(self, choices: PlayDecision, callable: Callable, **kwargs):
        super().__init__(**kwargs)
        self.callable = callable
        for action in PlayDecision:
            self.add_widget(
                PlayDecisionButton(action, disabled=not (action in choices))
            )

    def on_decision(self, widget, decision):
        print(f"will pass decision: {decision}")
        self.callable(decision)


class InsuranceButtons(BoxLayout):
    decision = ObjectProperty()

    def __init__(self, callable: Callable, **kwargs) -> None:
        super().__init__(**kwargs)
        self.callable = callable

    def yes(self, *args):
        self.decision = True

    def no(self, *args):
        self.decision = False

    def on_decision(self, _, decision):
        print(f"Will return decision: {decision}")
        self.callable(decision)


class KivyBettingStrategy(Slider):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min = engine.TABLE_LIMITS[0]
        self.max = engine.TABLE_LIMITS[1]
        self.step = self.min

    def bet(self, *args: Any, **kwargs: Any) -> float:
        self.disabled = True
        return self.value


class WelcomeScreen(Popup):
    pass


class PlayerCardView(RelativeLayout):
    cards = ListProperty()
    x_card_offset = 35
    y_card_offset = 6

    def __init__(
        self, hand: Hand, result: float | None = None, compact: bool = False, **kwargs
    ):
        super().__init__(**kwargs)
        if compact:
            self.compact_card_offset()
        self.result = result
        self.hand = hand
        self.cards = [*hand]

    def compact_card_offset(self):
        self.x_card_offset = 18
        self.y_card_offset = 23

    def on_cards(self, *args, **kwargs) -> None:
        self.clear_widgets()
        x = 0
        y = 0
        for card in self.cards:
            self.add_widget(
                Image(
                    source=f"./cards/{card.rank.lower()}_{card.suit.lower()}.png",
                    pos=(x, y),
                    size_hint_x=1.1,
                )
            )
            x += self.x_card_offset
            y += self.y_card_offset
        if len(self.cards) > 1:
            self.add_widget(PointsLabel(text=self.points_label_str(), pos=(x + 55, 0)))
        if self.result is not None:
            self.add_widget(
                Label(
                    text=self.bust_or_blackjack(self.hand)
                    or self.translate_result(self.result),
                    font_size="25dp",
                    pos_hint={"center_x": 0.5, "center_y": 0.1},
                )
            )

    def points_label_str(self) -> str:
        return str(self.hand.value)

    @staticmethod
    def bust_or_blackjack(hand: Hand) -> str | None:
        if hand.is_blackjack():
            return "BJ"
        elif hand.is_bust():
            return "BUST"

    @staticmethod
    def translate_result(result: float) -> str:
        if result > 0:
            return "WIN"
        elif result < 0:
            return "LOSS"
        else:
            return "PUSH"


class DealerCardView(PlayerCardView):
    x_card_offset = 35
    y_card_offset = 0

    def points_label_str(self) -> str:
        return self.bust_or_blackjack(self.hand) or super().points_label_str()


class PointsLabel(Label):
    pass


class DealButton(BoxLayout):
    pass


class Screen(BoxLayout):

    playerhands = ListProperty()
    dealercards = ListProperty()
    player_screen = ObjectProperty()
    dealer_screen = ObjectProperty()
    buttonstrip = ObjectProperty()
    cash_label = ObjectProperty()
    bet_size = ObjectProperty()
    result_message = StringProperty()
    shoe = ObjectProperty()

    pos_para = NumericProperty(0.4)
    pos_para_dealer = NumericProperty(0.4)
    hand_spacing = NumericProperty(100)

    round = ObjectProperty()
    decision_widget = ObjectProperty(allownone=True)
    cards = ListProperty()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.game = Game([Player(None, self.bet_size)])

        # self.x_card_offset = 35
        # self.y_card_offset = 6

        self.no_cash_text = {
            "button_text": "Close",
            "label_text": "You don't have enough cash for this bet",
            "title": "No Cash",
        }

        self.start_over_text = {
            "button_text": "Play Again",
            "label_text": "You lost all your money!!!\n\nYou make me sick you STUPID FUCK.",
            "title": "Stupid Fuck",
        }

    def update(self, *args):
        self.decision_widget = self.game.round.decision_callable
        self.dealercards = self.game.dealer.hand
        self.playerhands = [hand_play for hand_play in self.game.round.table.hands]
        self.cards = [card for hand_play in self.playerhands for card in hand_play.hand]
        self.cash_label.text = "{:,.0f}".format(self.game.players[0].cash)
        shoe = self.game.dealer.shoe
        self.shoe.text = (
            f"DECKS: {"\n"}"
            f"{(len(shoe)-shoe._cut_card)/52:.1f}"
            f"{"\n"} {"SHUFFLE" if shoe.will_shuffle else ""}"
        )

    def welcome(self):
        WelcomeScreen().open()

    def on_decision_widget(self, screen, decision):
        if isinstance(decision, InsuranceDecisionCallable):
            self.buttonstrip.clear_widgets()
            self.buttonstrip.add_widget(InsuranceButtons(decision))
        elif isinstance(decision, PlayDecisionCallable):
            self.buttonstrip.clear_widgets()
            assert self.round
            self.buttonstrip.add_widget(DecisionButtons(self.round.choices, decision))
        elif decision is None:
            self.buttonstrip.clear_widgets()
            self.buttonstrip.add_widget(DealButton())
            self.bet_size.disabled = False
            self.on_cards()

    def play(self, *args, **kwargs):
        self.game.play()
        self.round = self.game.round

    def on_cards(self, *args):
        self.player_screen.clear_widgets()
        for hand_play in self.playerhands:
            self.player_screen.add_widget(
                PlayerCardView(
                    hand_play.hand,
                    result=hand_play.result if hand_play.is_done else None,
                )
            )

    def on_dealercards(self, *args):
        print(f"INSIDE DEALERCARDS")
        self.dealer_screen.clear_widgets()
        self.dealer_screen.add_widget(DealerCardView(self.game.dealer.hand))

    def no_cash_popup(self, t):
        def action_post_dismiss(instance):
            if c.game_over:
                self.play_again()
            else:
                pass

        btnclose = Button(text=t["button_text"], size_hint_y=None, height="40sp")
        content = BoxLayout(orientation="vertical")
        content.add_widget(
            Label(text=t["label_text"], halign="center", font_size="20sp")
        )
        content.add_widget(btnclose)
        self.popup = Popup(
            title=t["title"],
            content=content,
            size_hint=(0.5, 0.5),
            auto_dismiss=False,
            title_align="center",
        )
        btnclose.bind(on_release=self.popup.dismiss)
        self.popup.bind(on_dismiss=action_post_dismiss)
        self.popup.open()

    def play_again(self):
        c.start_over()
        self.start_screen()

    def start_screen(self):
        self.dealer_screen.clear_widgets()
        self.player_screen.clear_widgets()
        self.buttonstrip.clear_widgets()
        self.bet_size.disabled = False
        self.buttonstrip.add_widget(DealButton())
        self.cash_label.text = "{:,.0f}".format(self.game.players[0].cash)
        self.welcome = WelcomeScreen()
        self.welcome.open()


class BlackjackApp(App):

    def build(self):
        self.screen = Screen()
        Clock.schedule_interval(self.screen.update, 0.25)
        return self.screen


if __name__ == "__main__":
    BlackjackApp().run()
