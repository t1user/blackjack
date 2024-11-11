from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from kivy.app import App
from kivy.graphics import Color, Line
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.settings import SettingNumeric, SettingOptions, SettingsWithSidebar
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

from blackjack import strategies
from blackjack.engine import (
    CONFIG,
    BettingStrategy,
    Card,
    DecisionHandler,
    Game,
    GameStrategy,
    Hand,
    HandPlay,
    PlayDecision,
    Player,
    Round,
    YesNoDecision,
)

root_dir = Path(__file__).parent

# this is the only number you should change
# 1 is the middle ground that should be acceptable on all devices
# for size optimization, use:
# 0.8-1.0 on desktop, and
# 1.0-1.2 on mobile
MAGNIFICATION = 1.2

SIZE_RATIO = 0.65  # percentage of play area over which cards are to be distributed
HORIZONTAL_STRETCH = 1.25  # ratio by which card ellipse is to be stretched horizontally
IMAGE_HEIGHT_RATIO = 0.26 * MAGNIFICATION  # image height as proportion of window height


class CountButton(ToggleButton):
    """
    This is the button that reveals and hides current count. It's defined in kv.
    """

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
    """
    Holder of buttons through which player makes play decisions about a hand.
    """

    decision = ObjectProperty()

    def __init__(self, callable: Callable, choices: PlayDecision, Hand, **kwargs):
        super().__init__(**kwargs)
        self.callable = callable
        for action in (
            PlayDecision if CONFIG["surrender"] else PlayDecision.no_surrender()
        ):
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

    max_bet = NumericProperty(CONFIG["player_cash"])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset()

    def bet(self, *args: Any, **kwargs: Any) -> float:
        self.disabled = True
        return self.value

    def on_max_bet(self, *args):
        self.max = min(CONFIG["table_limits"][1], self.max_bet)

    def reset(self):
        self.min = CONFIG["table_limits"][0]
        self.max = CONFIG["table_limits"][1]
        self.step = self.min


class DealButton(Button):
    # defined in kv
    pass


class CardImage(Image):
    def __init__(self, card: Card, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.source = f"{root_dir}/cards/{card.rank.lower()}_{card.suit.lower()}.png"
        self.width = self.height / 1.452  # this is the ratio of actual image file


class RotatedCardImage(CardImage):
    # defined in kv
    angle = NumericProperty(90)


class HandWidget(Widget):

    _offset = 0.15, 0.15

    def __init__(
        self, image_height: float, pos: tuple[float, float], hand: Hand, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.image_height = image_height
        self.center = pos
        self.hand = hand
        if len(self.hand) > 0:
            self.render()

    @property
    def offset(self):
        return (
            self._offset[0] * self.image_height,
            self._offset[1] * self.image_height,
        )

    def render(self):
        for i, card in enumerate(self.hand):
            self.add_widget(
                image := CardImage(
                    card,
                    height=self.image_height,
                    center=self._offset_position(i),
                )
            )
        self.add_widget(
            Label(
                text=self.hand.value_str(),
                center=self._label_position(image, i),
                font_size=self.image_height * 0.15,
            )
        )

    def _offset_position(self, n):
        return (
            self.center[0] + self.offset[0] * n,
            self.center[1] + self.offset[1] * n,
        )

    def _label_position(self, image: Image, n=0):
        return image.center[0], image.top + image.height * 0.1


class PlayerHand(HandWidget):

    _offset = 0.125, 0.125

    def __init__(
        self,
        image_height: float,
        pos: tuple[float, float],
        hand_play: HandPlay,
        active: bool = False,
        **kwargs,
    ) -> None:
        Widget.__init__(self, **kwargs)
        self.image_height = image_height
        self.center = pos
        self.hand = hand_play.hand
        self.hand_play = hand_play
        if len(self.hand) > 0:
            self.render()
        if active:
            with self.canvas.before:  # type: ignore
                Color(1, 0, 0)  # Set color to red
                self.frame = Line(
                    rectangle=self.get_bounding_box(), width=2
                )  # Draw the red frame
                self.bind(pos=self.update_frame, size=self.update_frame)  # type: ignore

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
        return (min_x * 0.975, min_y * 0.9, max_x * 1.05 - min_x, max_y * 1.15 - min_y)

    def update_frame(self, *args):
        # Update frame to match the computed bounding box
        bbox = self.get_bounding_box()
        self.frame.rectangle = bbox

    def render(self):
        if not self.hand_play.doubled:
            super().render()
        else:
            new_hand = self.hand.copy()
            last_card = new_hand.pop()
            for i, card in enumerate(new_hand):
                self.add_widget(
                    image := CardImage(
                        card,
                        height=self.image_height,
                        center=self._offset_position(i),
                    )
                )
            self.add_widget(
                rotated_image := RotatedCardImage(
                    last_card,
                    height=self.image_height,
                    center=(
                        self._offset_position(i + 2.1)[0],
                        self._offset_position(i + 1.25)[1],
                    ),
                )
            )
            self.add_widget(
                Label(
                    text=self.hand.value_str(),
                    center=(rotated_image.center[0], self._label_position(image, i)[1]),
                    font_size=self.image_height * 0.15,
                )
            )
        self.add_widget(
            Label(
                text=self.result_str(),
                color=(1, 0, 0) if self.hand_play.result < 0 else (0, 1, 0),
                center=(
                    self.center_x,
                    self.children[-1].top - self.image_height * 1.075,
                ),
                font_size=self.image_height * 0.15,
                font_name="data/fonts/Roboto-Bold.ttf",
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
    felt_image = StringProperty(f"{root_dir}/felt.jpg")
    size_shrinker = 1

    def on_size(self, *args):
        self.update()

    @property
    def image_height(self):
        return (
            IMAGE_HEIGHT_RATIO * self.height
            if len(self.playerhands) < 8
            else IMAGE_HEIGHT_RATIO * self.height * 0.8
        )

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
            hand_widget = PlayerHand(self.image_height, position, hand, active)
            self.add_widget(hand_widget)

    def dealer_hand(self) -> None:
        if self.dealercards:
            position = self.get_position(-0.5)
            hand_widget = DealerHand(self.image_height, position, self.dealercards)
            self.add_widget(hand_widget)

    def get_player_position_indexes(self, n: int):
        # n is number of hands to spread out
        if n == 1:
            return [0.5]
        elif n == 2:
            return [0.2, 0.8]
        elif n == 3:
            return [0.15, 0.5, 0.85]
        else:
            return list(self.divider(n))

    @staticmethod
    def divider(n):
        counter = 1
        i = 0
        while counter <= n:
            if counter == n:
                yield 1
            else:
                yield i
            i += round(1 / (n - 1), 2)
            counter += 1

    def get_position(self, t):
        """Return position coordinates on an ellipse for a position index t.
        t must be in the range <-1,1>.
        players are positioned in the area <0, 1>
        dealer is always at position -0.5
        """
        assert -1 <= t <= 1
        height = SIZE_RATIO * self.height / 2
        width = HORIZONTAL_STRETCH * SIZE_RATIO * self.width / 2
        t_ = abs(t)
        x = width - 2 * (t_ * width)
        y = -height / width * (width**2 - x**2) ** 0.5
        if t < 0:
            y = -y
        return self.offset(x, y)

    def offset(self, x, y):
        # center is offset to the left and up
        return self.center[0] * 0.95 + x, self.center[1] * 1.025 + y


class Screen(BoxLayout):

    playarea = ObjectProperty()
    buttonstrip = ObjectProperty()
    cash_label = ObjectProperty()
    bet_size = ObjectProperty()
    shoe = ObjectProperty()
    count_button = ObjectProperty()
    welcome_screen = ObjectProperty()

    playing_player = None

    def __init__(self, config, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        Hand.newCardEvent += self.update
        DecisionHandler.newDecisionEven += self.on_decision_widget
        Round.cashOutEvent += self.update
        self.game = self.start()

    def update(self, *args):
        cash = self.playing_player.cash  # type: ignore
        self.playarea.dealercards = self.game.dealer.hand
        self.playarea.playerhands = list(
            reversed([hand_play for hand_play in self.game.round.table.hands])
        )
        self.count_button.count = self.game.dealer.shoe.hilo_count
        self.cash_label.text = "${:>5,.2f}".format(cash)
        shoe = self.game.dealer.shoe
        self.shoe.text = (
            f"DECKS: "
            f"{(len(shoe)-shoe._cut_card)/52:.1f} "
            f"{'SHUFFLE' if shoe.will_shuffle else ''}"
        )
        self.bet_size.max_bet = cash
        self.playarea.update()

    def on_number_of_hands(self, hands: int) -> None:
        if self.playing_player is not None:
            self.playing_player.number_of_hands = hands

    def update_npc(self):
        player_config = dict(self.config["players"])
        npcs = PlayerFactory(player_config, self.bet_size).npcs
        assert self.playing_player
        npcs.insert(1, self.playing_player)
        players = [player for player in npcs if player]
        self.game.players = players

    def on_decision_widget(self, decision):
        self.buttonstrip.clear_widgets()
        assert self.playing_player
        if decision is None or decision.choices is None:
            self.buttonstrip.add_widget(DealButton())
            self.bet_size.disabled = False
        elif isinstance(decision.choices, YesNoDecision):
            self.buttonstrip.add_widget(
                InsuranceButtons(decision, decision.choices, decision.hand)
            )
        elif isinstance(decision.choices, PlayDecision):
            self.bet_size.disabled = True
            self.buttonstrip.add_widget(
                DecisionButtons(decision, decision.choices, decision.hand)
            )
        self.update()

    def play(self, *args, **kwargs):
        self.game.play()

    def start(self, *args) -> Game:
        player_config = dict(self.config["players"])
        assert player_config is not None
        self.bet_size.reset()
        players = PlayerFactory(player_config, self.bet_size).players
        if len(players) == 1 and players[0].number_of_hands == 0:
            players[0].number_of_hands = 1
        self.game = Game(players)

        playing_player = [
            player for player in self.game.players if player.strategy is None
        ]
        assert len(playing_player) == 1
        self.playing_player = playing_player[0]
        # initialize buttons
        self.on_decision_widget(None)
        return self.game


@dataclass
class PlayerFactory:
    """
    Creates appropriate players based on provided config from settings.
    """

    config: dict[str, str]
    betting_strategy: BettingStrategy

    @property
    def players(self):
        return self.player_factory()

    @property
    def npcs(self):
        return self.npc_factory()

    def player_factory(
        self,
    ) -> list[Player]:
        players = self.npc_factory()
        players.insert(
            1,
            Player(
                None,
                self.betting_strategy,
                number_of_hands=int(self.config["number_of_hands"]),
            ),
        )
        return [player for player in players if player]

    def npc_factory(self) -> list[Player]:
        npc_players = []
        for param in ("l_strategy", "r_strategy"):
            strategy_str = self.config.get(param)
            assert strategy_str is not None
            strategy_cls = self._translate_strategy_config(strategy_str)
            if strategy_cls is not None:
                npc_players.append(
                    Player(
                        strategy_cls(),
                        strategies.FixedBettingStrategy(
                            max(
                                round(CONFIG["player_cash"] * 0.025, 0),
                                CONFIG["table_limits"][0],
                            )
                        ),
                    )
                )
            else:
                npc_players.append(None)
        return npc_players

    @staticmethod
    def _translate_strategy_config(item: str) -> type[GameStrategy] | None:
        if not hasattr(strategies, item):
            return None
        elif not issubclass(getattr(strategies, item), GameStrategy):
            return None
        return getattr(strategies, item)


class PercentSettingNumeric(SettingNumeric):
    def _validate(self, instance):
        text_type = str
        is_float = "." in str(self.value)
        self._dismiss()
        try:
            if is_float:
                value = float(self.textinput.text)
            else:
                value = int(self.textinput.text)
            if not (5 <= value <= 95):  # type: ignore
                raise ValueError
            self.value = text_type(value)
        except ValueError:
            return


class PositiveSettingNumeric(SettingNumeric):
    def _validate(self, instance):
        text_type = str
        is_float = "." in str(self.value)
        self._dismiss()
        try:
            if is_float:
                value = float(self.textinput.text)
            else:
                value = int(self.textinput.text)
            if not 0 < value:
                raise ValueError
            self.value = text_type(value)
        except ValueError:
            return


class FractionSettingOptions(SettingOptions):
    def _set_option(self, instance):
        self.value = {"3/2": "1.5", "6/5": str(6 / 5), "1/1": str(1)}.get(instance.text)
        self.popup.dismiss()


rules_types = {key: type(value) for key, value in CONFIG.items()}
function_dict = {int: "getint", float: "getfloat", bool: "getboolean"}


class BlackjackApp(App):

    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        self.screen = Screen(self.config)
        return self.screen

    def build_config(self, config):
        config.setdefaults(
            "players",
            {
                "number_of_hands": 1,
                "r_strategy": None,
                "l_strategy": None,
            },
        )
        config.setdefaults("rules", CONFIG.copy())

    def load_config(self):
        config = super().load_config()
        self.update_config(config)
        return config

    def update_config(self, config):
        for key, value in config["rules"].items():
            self.on_config_change(config, "rules", key, value)

    def build_settings(self, settings):
        settings.register_type("percent_numeric", PercentSettingNumeric)
        settings.register_type("fraction_options", FractionSettingOptions)
        settings.register_type("positive_numeric", PositiveSettingNumeric)

        with open(root_dir / "settings_players.json", "rt") as player_json:
            settings.add_json_panel("Players", self.config, data=player_json.read())

        with open(root_dir / "settings_rules.json", "rt") as rules_json:
            settings.add_json_panel("Rules", self.config, data=rules_json.read())

    def on_config_change(self, config, section, key, value):
        if section == "rules":
            method = function_dict.get(rules_types[key], "get")
            callable = getattr(config, method, "get")
            result = callable("rules", key)  # type: ignore
            if isinstance(result, str):
                result = eval(result)
            CONFIG[key] = result
        elif section == "players":
            if key == "number_of_hands":
                self.screen.on_number_of_hands(int(value))  # type: ignore
            else:
                self.screen.update_npc()


def run():
    BlackjackApp().run()


if __name__ == "__main__":
    run()
