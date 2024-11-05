import math
from typing import Any, Callable

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

from blackjack import engine
from blackjack.engine import (
    DecisionHandler,
    Game,
    Hand,
    HandPlay,
    PlayDecision,
    Player,
    Round,
    YesNoDecision,
)
from blackjack.strategies import FixedBettingStrategy, MimickDealer, RandomStrategy

SIZE_RATIO = 0.65  # percentage of play area over which cards are to be distributed
IMAGE_HEIGHT_RATIO = 0.15  # image height as proportion of window height


class CountButton(ToggleButton):
    count = NumericProperty(0.0)

    def on_count(self, *args):
        self.text = self.get_text()

    def get_text(self, *args) -> str:
        return str(self.count) if self.state == "down" else "COUNT"


class PlayDecisionButton(Button):
    action = ObjectProperty()

    def __init__(self, action: PlayDecision | YesNoDecision, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self.text = action.name

    def on_release(self, **kwargs):
        super().on_release(**kwargs)
        self.parent.decision = self.action


class DecisionButtons(BoxLayout):
    decision = ObjectProperty()

    def __init__(self, callable: Callable, choices: PlayDecision, Hand, **kwargs):
        super().__init__(**kwargs)
        self.callable = callable
        for action in PlayDecision:
            self.add_widget(
                PlayDecisionButton(action, disabled=not (action in choices))
            )

    def on_decision(self, widget, decision):
        self.callable(decision)


class YesNoButton(PlayDecisionButton):
    pass


class InsuranceButtons(BoxLayout):
    decision = ObjectProperty()

    def __init__(
        self, callable: Callable, choices: YesNoDecision, hand: Hand, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.callable = callable
        self.children[0].text = "EVEN MONEY?" if hand.is_blackjack() else "INSURANCE?"
        for action in YesNoDecision:
            self.add_widget(YesNoButton(action))

    def on_decision(self, _, decision):
        self.callable(decision)


class KivyBettingStrategy(Slider):

    max_bet = NumericProperty(engine.PLAYER_CASH)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min = engine.TABLE_LIMITS[0]
        self.max = engine.TABLE_LIMITS[1]
        self.step = self.min

    def bet(self, *args: Any, **kwargs: Any) -> float:
        self.disabled = True
        return self.value

    def on_max_bet(self, *args):
        self.max = min(engine.TABLE_LIMITS[1], self.max_bet)


class DealButton(BoxLayout):
    pass


class TextLabel(Label):
    pass


class HandWidget(Widget):

    _offset = 0.15, 0.15

    def __init__(self, pos: tuple[float, float], hand: Hand, **kwargs) -> None:
        super().__init__(**kwargs)
        self.center = pos
        self.hand = hand
        if len(self.hand) > 0:
            self.render()

    @property
    def image_height(self):
        return Window.height * IMAGE_HEIGHT_RATIO

    @property
    def offset(self):
        return (
            self._offset[0] * self.image_height,
            self._offset[1] * self.image_height,
        )

    def render(self):
        for i, card in enumerate(self.hand):
            self.add_widget(
                image := Image(
                    source=f"cards/{card.rank.lower()}_{card.suit.lower()}.png",
                    center=self._offset_position(i),
                    height=self.image_height,
                )
            )
        self.add_widget(
            Label(
                text=self.points_value_str(),
                center=self._label_position(image, i),
                font_size=self.image_height * 0.2,
            )
        )

    def _offset_position(self, n):
        return (
            self.center[0] + self.offset[0] * n,
            self.center[1] + self.offset[1] * n,
        )

    def _label_position(self, image: Image, n=0):
        # return self._offset_position(n - 1)[0], image.top + 10
        return image.center[0], image.top + image.height * 0.15

    def points_value_str(self):
        return self.hand.value_str()


class PlayerHand(HandWidget):

    _offset = 0.15, 0.15

    def __init__(
        self,
        pos: tuple[float, float],
        hand_play: HandPlay,
        active: bool = False,
        **kwargs,
    ) -> None:
        Widget.__init__(self, **kwargs)
        self.center = pos
        self.hand = hand_play.hand
        self.hand_play = hand_play
        if len(self.hand) > 0:
            self.render()
        if active:
            with self.canvas.before:
                Color(1, 0, 0)  # Set color to red
                self.frame = Line(
                    rectangle=self.get_bounding_box(), width=1
                )  # Draw the red frame
                self.bind(pos=self.update_frame, size=self.update_frame)

    def get_bounding_box(self):
        # Initialize with the widget's own position and size
        min_x, min_y = self.x, self.y
        max_x, max_y = self.right, self.top

        # Iterate over children to get the true bounding box
        for child in self.children:
            if not isinstance(child, Image):
                continue
            child_min_x, child_min_y = child.to_window(*child.pos)
            child_max_x, child_max_y = (
                child_min_x + child.width,
                child_min_y + child.height,
            )

            # Update min and max values to include child bounds
            min_x, min_y = min(min_x, child_min_x), min(min_y, child_min_y)
            max_x, max_y = max(max_x, child_max_x), max(max_y, child_max_y)

        # Return bounding box coordinates
        return (min_x, min_y * 0.9, max_x - min_x, max_y * 1.15 - min_y)

    def update_frame(self, *args):
        # Update frame to match the computed bounding box
        bbox = self.get_bounding_box()
        self.frame.rectangle = bbox

    def render(self):
        super().render()
        self.add_widget(
            Label(
                text=self.result_str(),
                color=(1, 0, 0) if self.hand_play.result < 0 else (0, 1, 0),
                center=(self.center_x, self.top - self.height * 1.1),
                font_size=self.image_height * 0.2,
            )
        )

    def result_str(self) -> str:
        if not self.hand_play._is_cashed:
            return ""
        else:
            result = self.hand_play.result
            if not result:
                return "PUSH"
            else:
                return f"+{result}" if result > 0 else str(result)


class DealerHand(HandWidget):

    _offset = 1, 0

    def _offset_position(self, n):
        offset = self.offset[0]
        if len(self.hand) > 4:
            n = n - len(self.hand) + 4
        if len(self.hand) > 5:
            offset = self.offset[0] * 0.75
        return (self.center[0] + offset * (n - 1), self.center[1])

    def _label_position(self, image: Image, n=0) -> tuple[float, float]:
        if len(self.hand) > 4:
            n = n - len(self.hand) + 4
        return self.center[0] + self.offset[0] * (n - 0.25), self.center[1]

    def points_value_str(self) -> str:
        return self.hand.dealer_value_str()


class PlayArea(Widget):
    playerhands: list[HandPlay] = []
    dealercards: Hand = Hand()

    def update(self, *args):
        self.clear_widgets()
        self.dealer_hand()
        self.player_hands()

    def player_hands(self):
        if len(self.playerhands) == 0:
            return
        for position_index, hand in zip(
            self.get_player_position_indexes(len(self.playerhands)), self.playerhands
        ):
            position = self.get_position(position_index)
            active = hand.active if len(self.playerhands) > 1 else False
            hand_widget = PlayerHand(position, hand, active)
            self.add_widget(hand_widget)

    def get_player_position_indexes(self, n: int):
        # n is number of hands to spread out
        if n == 1:
            return [0.5]
        elif n == 2:
            return [0.2, 0.8]
        elif n == 3:
            return [0.15, 0.5, 0.85]
        elif n == 4:
            return [0, 0.3, 0.6, 0.9]
        elif n == 5:
            return [0, 0.25, 0.5, 0.75, 1]
        else:
            return list(
                map(
                    lambda x: x / 1000,
                    range(0, 1000 + (step := int(1 / n * 1000)), step),
                )
            )

    def dealer_hand(self) -> None:
        if self.dealercards:
            position = self.get_position(-0.5)
            hand_widget = DealerHand(position, self.dealercards)
            self.add_widget(hand_widget)

    def get_position(self, t):
        """Return position coordinates on an ellipse for a position index t.
        t must be in the range -1,1.
        players are position in the area 0, 1
        dealer is always at position -0.5
        """
        assert -1 <= t <= 1
        height = SIZE_RATIO * self.height / 2
        width = SIZE_RATIO * self.width / 2
        t_ = abs(t)
        x = width - 2 * (t_ * width)
        y = -height / width * math.sqrt(width**2 - x**2)
        if t < 0:
            y = -y
        return self.offset(x, y)

    def offset(self, x, y):
        return self.center[0] + x, self.center[1] + y


class Screen(BoxLayout):

    playarea = ObjectProperty()
    buttonstrip = ObjectProperty()
    cash_label = ObjectProperty()
    bet_size = ObjectProperty()
    shoe = ObjectProperty()
    count_button = ObjectProperty()
    welcome_screen = ObjectProperty()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        Hand.newCardEvent += self.update
        DecisionHandler.newDecisionEven += self.on_decision_widget
        Round.cashOutEvent += self.update
        self.game = self.start()

    def update(self, *args):
        self.playarea.dealercards = self.game.dealer.hand
        self.playarea.playerhands = list(
            reversed([hand_play for hand_play in self.game.round.table.hands])
        )
        self.count_button.count = self.game.dealer.shoe.hilo_count
        self.cash_label.text = "${:>5,.2f}".format(self.game.players[0].cash)
        shoe = self.game.dealer.shoe
        self.shoe.text = (
            f"DECKS: "
            f"{(len(shoe)-shoe._cut_card)/52:.1f} "
            f"{"SHUFFLE" if shoe.will_shuffle else ""}"
        )
        self.bet_size.max_bet = self.game.players[0].cash
        self.playarea.update()

    def on_decision_widget(self, decision):
        self.buttonstrip.clear_widgets()
        if decision is None or decision.choices is None:
            self.buttonstrip.add_widget(DealButton())
            self.bet_size.disabled = False
        elif isinstance(decision.choices, YesNoDecision):
            self.buttonstrip.add_widget(
                InsuranceButtons(decision, decision.choices, decision.hand)
            )
        elif isinstance(decision.choices, PlayDecision):
            self.buttonstrip.add_widget(
                DecisionButtons(decision, decision.choices, decision.hand)
            )
        self.update()

    def play(self, *args, **kwargs):
        self.game.play()

    def start(self, *args) -> Game:
        self.game = Game(
            [
                Player(None, self.bet_size),
                Player(MimickDealer(), FixedBettingStrategy(25)),
                Player(RandomStrategy(), FixedBettingStrategy(50)),
            ]
        )
        self.on_decision_widget(None)
        self.update()
        return self.game


class BlackjackApp(App):

    def build(self):
        self.screen = Screen()
        # Clock.schedule_interval(self.screen.update, 0.25)
        return self.screen


if __name__ == "__main__":
    BlackjackApp().run()
