#!/usr/local/bin/python3

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.properties import ListProperty, ObjectProperty

from blackjack import *

from copy import deepcopy

class CardView(RelativeLayout):
    pass

class CardImage(Image):
    pass

class PointsLabel(Label):
    pass

class Screen(BoxLayout):
    
    playerhands = ListProperty()
    dealercards = ListProperty()
    player_screen = ObjectProperty()
    dealer_screen = ObjectProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.playerhands = player.hands
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
        return screen
    
    def on_playerhands(self, *args):
        self.player_screen.clear_widgets()
        for hand in self.playerhands:
            cardview = CardView()
            screen = self.update_player_hand(cardview, hand)
            self.player_screen.add_widget(screen)
        
    def update_player_hand(self, screen, hand):
        self.k_play(screen, hand)
        screen.add_widget(Label(
        text='',
        font_size='25dp',
        pos_hint={'center_x': .6, 'center_y': 1}
        ))
        return screen
        
    def on_dealercards(self, *args):
        self.k_play(self.dealer_screen, dealer.hand)
        
    def hit(self):
        a = player.hands.pop()
        a.deal()
        player.hands.append(a)        
        self.playerhands = deepcopy(player.hands)
        print (self.playerhands)
    
    def double(self):
        dealer.hand.deal()
        self.dealercards = dealer.hand.cards
    
    def split(self):
        index = player.hands.index(player_hand)
        player.hands.remove(player_hand)
        i = 0
        for card in player_hand.cards:
            split_hand = Hand(card, 5, shoe=shoe)
            #split_hand.set_split()
            player.hands.insert(index + i, split_hand)
            i += 1
        self.playerhands = deepcopy(player.hands)
        
             
class Bj4App(App):
    def build(self):
        return Screen()
        
    
if __name__ == '__main__':
    shoe = Shoe()
    player = Player()
    player_hand = Hand(bet=5, shoe=shoe)
    dealer = Dealer(shoe=shoe)
    player_hand.deal()
    player.hands.append(player_hand)
    
    Bj4App().run()


