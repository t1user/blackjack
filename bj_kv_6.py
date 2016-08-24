#!/usr/local/bin/python3

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.properties import ListProperty, ObjectProperty, NumericProperty

from blackjack_1 import Controller

from copy import deepcopy

class CardView(RelativeLayout):
    pass

class PointsLabel(Label):
    pass

class PlayActionButtons(BoxLayout):
    
    stay_button = ObjectProperty()

    def hit(self):
        c.hit(c.player_hand)
        s.playerhands = deepcopy(c.player.hands)
        self.stay_button.disabled = True
        
    def double(self):
        c.double(c.player_hand)
        s.playerhands = deepcopy(c.player.hands)   
    
    def split(self):
        c.split(c.player_hand)
        s.playerhands = deepcopy(c.player.hands)
    
    def stay(self):
        c.stand(c.player_hand)

    
class Screen(BoxLayout):
    
    playerhands = ListProperty()
    dealercards = ListProperty()
    player_screen = ObjectProperty()
    dealer_screen = ObjectProperty()
    buttonstrip = ObjectProperty()
    cash_label = ObjectProperty()
    bet_size = ObjectProperty()
    
    pos_para = NumericProperty(.4)
    pos_para_dealer = NumericProperty(.4)
    hand_spacing = NumericProperty(100)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.playerhands = c.player.hands
        self.dealercards = c.dealer.hand.cards
        
        self.x_card_offset = 35
        self.y_card_offset = 6
        
        self.buttonstrip.add_widget(PlayActionButtons())
        
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
            pos = (x + 40, 0)
            ))
        return screen
    
    def on_playerhands(self, *args):
        self.player_screen.clear_widgets()
        self.hand_spacing = max(150 - max(len(self.playerhands)-3, 0)
         * 75, 20)
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
        text='',
        font_size='25dp',
        pos_hint={'center_x': .5, 'center_y': .1}
        ))
        self.cash_label.text = '{:,}'.format(c.player.cash)
        return screen
        
    def on_dealercards(self, *args):
        self.x_card_offset = 35
        self.y_card_offset = 0
        if len(c.dealer.hand.cards) > 6:
            self.pos_para_dealer = 0.2
        self.k_play(self.dealer_screen, c.dealer.hand)
         
         
class Bj6App(App):
    def build(self):
        global s
        s = Screen()
        return s
        
        
if __name__ == '__main__':
    c = Controller()
    c.run()
    
    Bj6App().run()


