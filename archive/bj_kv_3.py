#!/usr/local/bin/python3

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.properties import ListProperty, ObjectProperty
from blackjack import *

class CardView(RelativeLayout):
    pass

class CardImage(Image):
    pass

class PointsLabel(Label):
    pass

class Screen(BoxLayout):
    
    playercards = ListProperty()
    dealercards = ListProperty()
    player_screen = ObjectProperty()
    dealer_screen = ObjectProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.playercards = player_hand.cards
        self.dealercards = dealer.hand.cards
        
    def k_play(self, screen, hand):
        screen.clear_widgets()
        x = 0
        for i in hand.cards:
            screen.add_widget(CardImage(source=
            './Cards/'+i.rank.lower()+'_'+ i.suit.lower()+'.png',
             pos=(x,0)))
            x += 35
        if len(hand.cards) > 1:
            screen.add_widget(PointsLabel(text=str(hand.get_value()), 
            pos = (x + 40, 0)
            ))
        
    def on_playercards(self, *args):
        self.k_play(self.player_screen, player_hand)
        self.player_screen.add_widget(Label(
        text='This is a test',
        font_size='25dp',
        pos_hint={'center_x': 0.6, 'center_y': .9}
        ))
        
    def on_dealercards(self, *args):
        self.k_play(self.dealer_screen, dealer.hand)
        
    def hit(self):
        player_hand.deal()
        self.playercards = player_hand.cards
    
    def double(self):
        dealer.hand.deal()
        self.dealercards = dealer.hand.cards
        
             
class Bj3App(App):
    def build(self):
        return Screen()
        
    
if __name__ == '__main__':
    shoe = Shoe()
    player = Player()
    player_hand = Hand(bet=5, shoe=shoe)
    dealer = Dealer(shoe=shoe)
    player_hand.deal()
    player.hands.append(player_hand)
    
    Bj3App().run()


