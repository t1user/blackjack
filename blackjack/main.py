from copy import deepcopy

from kivy.app import App
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

from .engine import Controller


class WelcomeScreen(Popup):
    pass


class CardView(RelativeLayout):
    pass


class PointsLabel(Label):
    pass


class InsuranceButtons(BoxLayout):
    def yes(self):
        c.buy_insurance()
        s.game_controller()

    def no(self):
        c.decline_insurance()
        s.game_controller()


class PostEvaluationButtons(BoxLayout):
    def deal(self):
        if s.welcome:
            s.welcome.dismiss()
        s.bet_size.disabled = False
        c.player.bet = s.bet_size.value
        c.run()
        s.game_controller()

    def start_over(self):
        pass


class PlayActionButtons(BoxLayout):

    active_options = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.active_options = c.options

    def stand(self):
        c.stand(c.player_hand)
        s.game_controller()

    def split(self):
        c.split(c.player_hand)
        s.game_controller()

    def double(self):
        c.double(c.player_hand)
        s.game_controller()

    def hit(self):
        c.hit(c.player_hand)
        s.game_controller()


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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.x_card_offset = 35
        self.y_card_offset = 6

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

        self.popup = None

        self.start_screen()

    def game_controller(self):
        self.bet_size.min = min(25, c.player.cash)
        self.buttonstrip.clear_widgets()
        self.update_screen()
        self.bet_size.disabled = True
        if c.no_cash and not c.game_over:
            self.no_cash_popup(self.no_cash_text)
            c.no_cash = False
        if c.game_over:
            self.no_cash_popup(self.start_over_text)
            return
        if c.insurance_option:
            self.buttonstrip.add_widget(InsuranceButtons())
        else:
            c.player_input(c.player_hand)
            self.update_screen()
            if c.player_hand.played:
                self.bet_size.disabled = False
                self.update_screen()
                self.buttonstrip.add_widget(PostEvaluationButtons())
            else:
                self.buttonstrip.add_widget(PlayActionButtons())

    def update_screen(self):
        self.playerhands = deepcopy(c.player.hands)
        self.dealercards = c.dealer.hand.cards
        self.cash_label.text = "{:,.0f}".format(c.player.cash)
        self.shoe.text = "Shoe: {cards}\n({decks:,.1f} decks)\nCut: {cut_card:,.0f}\n({cut_card_decks:,.1f} decks)\n{shuffle}".format(
            cards=len(c.shoe.contents),
            decks=len(c.shoe.contents) / 52,
            cut_card=c.shoe.cut_card,
            cut_card_decks=c.shoe.cut_card / 52,
            shuffle=c.shoe.will_shuffle,
        )

    def k_play(self, screen, hand):
        screen.clear_widgets()
        x = 0
        y = 0
        for i in hand.cards:
            screen.add_widget(
                Image(
                    source="./Cards/" + i.rank.lower() + "_" + i.suit.lower() + ".png",
                    pos=(x, y),
                    size_hint_x=1.1,
                )
            )
            x += self.x_card_offset
            y += self.y_card_offset
        if len(hand.cards) > 1:
            screen.add_widget(PointsLabel(text=str(hand.get_value()), pos=(x + 52, 0)))
        return screen

    def on_playerhands(self, *args):
        self.player_screen.clear_widgets()
        # determines space between multiple hands
        self.hand_spacing = max(150 - max(len(self.playerhands) - 3, 0) * 65, 15)
        # determines left margin
        self.pos_para = max(0.4 - len(self.playerhands) / 10, 0)
        if len(self.playerhands) > 2:
            self.x_card_offset = 18
            self.y_card_offset = 23
        else:
            self.x_card_offset = 35
            self.y_card_offset = 6
        for hand in self.playerhands:
            cardview = CardView()
            screen = self.update_player_hand(cardview, hand)
            self.player_screen.add_widget(screen)

    def update_player_hand(self, screen, hand):
        self.k_play(screen, hand)
        screen.add_widget(
            Label(
                text=hand.result_message,
                font_size="25dp",
                pos_hint={"center_x": 0.5, "center_y": 0.1},
            )
        )
        self.cash_label.text = "{:,.0f}".format(c.player.cash)
        return screen

    def on_dealercards(self, *args):
        self.x_card_offset = 35
        self.y_card_offset = 0
        if len(c.dealer.hand.cards) > 6:
            self.pos_para_dealer = 0.2
        self.k_play(self.dealer_screen, c.dealer.hand)

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
        c.no_cash = False
        self.buttonstrip.add_widget(PostEvaluationButtons())
        self.cash_label.text = "{:,.0f}".format(c.player.cash)
        self.welcome = WelcomeScreen()
        self.welcome.open()


class Bj7App(App):
    def build(self):
        global s
        s = Screen()
        return s


if __name__ == "__main__":
    c = Controller()
    Bj7App().run()
