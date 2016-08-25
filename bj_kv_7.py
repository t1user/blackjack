#!/usr/local/bin/python3

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.properties import ListProperty, ObjectProperty, \
                            NumericProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.popup import Popup

from blackjack_1 import Controller

from copy import deepcopy

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
    
    pos_para = NumericProperty(.4)
    pos_para_dealer = NumericProperty(.4)
    hand_spacing = NumericProperty(100)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.playerhands = c.player.hands
        self.dealercards = c.dealer.hand.cards
        
        #self.result_message = hand.result_message
        
        self.x_card_offset = 35
        self.y_card_offset = 6
        
        self.game_controller()
    
    def game_controller(self):
        self.bet_size.min = min(25, c.player.cash)
        self.buttonstrip.clear_widgets()
        self.update_screen()
        self.bet_size.disabled = True
        if c.no_cash:
            self.no_cash_popup()
            c.no_cash = False
        if c.player.cash == 0:
            self.start_over_popup()
            self.play_again()
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
        self.cash_label.text = '{:,.0f}'.format(c.player.cash)
        self.shoe.text = 'Shoe: {cards}\n({decks:,.1f} decks)\nCut: {cut_card:,.0f}\n({cut_card_decks:,.1f} decks)\n{shuffle}'.format(
            cards=len(c.shoe.contents), decks=len(c.shoe.contents)/52,
             cut_card=c.shoe.cut_card, cut_card_decks=c.shoe.cut_card/52,
             shuffle = c.shoe.will_shuffle)
        
    def k_play(self, screen, hand):
        screen.clear_widgets()
        x = 0
        y = 0
        for i in hand.cards:
            screen.add_widget(Image(source=
            './Cards/'+i.rank.lower()+'_'+ i.suit.lower()+'.png',
             pos=(x,y)))
            x += self.x_card_offset
            y += self.y_card_offset
        if len(hand.cards) > 1:
            screen.add_widget(PointsLabel(text=str(hand.get_value()), 
            pos = (x + 48, 0)
            ))
        return screen
    
    def on_playerhands(self, *args):
        self.player_screen.clear_widgets()
        self.hand_spacing = max(150 - max(len(self.playerhands)-3, 0)
         * 65, 15)
        self.pos_para = max(.4 - len(self.playerhands)/10, 0)
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
        screen.add_widget(Label(
        text = hand.result_message,
        font_size = '25dp',
        pos_hint = {'center_x': .5, 'center_y': .1}
        ))
        self.cash_label.text = '{:,.0f}'.format(c.player.cash)
        return screen
        
    def on_dealercards(self, *args):
        self.x_card_offset = 35
        self.y_card_offset = 0
        if len(c.dealer.hand.cards) > 6:
            self.pos_para_dealer = 0.2
        self.k_play(self.dealer_screen, c.dealer.hand)
     
    def no_cash_popup(self):
        btnclose = Button(text='Close', size_hint_y=None, height='40sp')
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="You don't have enough cash for this bet"))
        content.add_widget(btnclose)
        popup = Popup(title = 'No Cash', 
                content = content, size_hint = (.5, .5),
                auto_dismiss=False)
        btnclose.bind(on_release=popup.dismiss)
        popup.open()
        
    def start_over_popup(self):
        btnclose = Button(text='Play Again', size_hint_y=None, height='40sp')
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="You lost all your money!!!\n\nYou make me sick you STUPID FUCK.",
        halign='center'))
        content.add_widget(btnclose)
        popup = Popup(title = 'Stupid Fuck', 
                content = content, size_hint = (.5, .5),
                auto_dismiss=False)
        btnclose.bind(on_release=popup.dismiss)
        popup.open()
    
    def play_again(self):
        c = Controller()
        c.run
        
        
class Bj7App(App):
    def build(self):
        global s
        s = Screen()
        return s
        
        
if __name__ == '__main__':
    c = Controller()
    c.run()
    
    Bj7App().run()


