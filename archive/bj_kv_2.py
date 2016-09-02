#!/usr/local/bin/python3

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, ObjectProperty
from blackjack import *

class CardView(BoxLayout):
    pass

class PlayArea(BoxLayout):
    
    playercards = ListProperty()
    
    def __init__ (self, **kwargs):
        super().__init__(**kwargs)

        self.playercards = player_hand.cards
        
        dealer_screen = CardView()
        player_screen = CardView()
        
        self.k_play(dealer_screen, dealer.hand)
        self.k_play(player_screen, player_hand)
        
        self.add_widget(dealer_screen)
        self.add_widget(player_screen)
        
        print(self.playercards)
        player_hand.delete()
        self.playercards = player_hand.cards
        print(self.playercards)
        self.playercards = player_hand.cards
        player_hand.deal()
        self.playercards = player_hand.cards
        print(self.playercards)
        
    def k_play(self, screen, hand):
        screen.clear_widgets()
        for i in hand.cards:
            screen.add_widget(i.image)
    
    def on_playercards(self, *args):
        #self.k_play(self.player_screen, self.player_hand)
        print(self.playercards)
        print(args)

class Screen(BoxLayout):
    
    playarea = ObjectProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def hit(self):
        player_hand.deal()
        playarea.playercards = player_hand.cards
        
             
class Bj2App(App):
    pass
        
    
if __name__ == '__main__':
    shoe = Shoe()
    player = Player()
    player_hand = Hand(bet=5, shoe=shoe)
    dealer = Dealer(shoe=shoe)
    player_hand.deal()
    player.hands.append(player_hand)
    
    Bj2App().run()


