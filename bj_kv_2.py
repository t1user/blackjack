#!/usr/local/bin/python3

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from blackjack import *

class CardView(BoxLayout):
    pass

class PlayArea(BoxLayout):
    
    playercards = ListProperty()
    
    def __init__ (self, **kwargs):
        super().__init__(**kwargs)

        playercards = player_hand.cards
                
        dealer_screen = CardView()
        player_screen = CardView()
        self.k_play(dealer_screen, dealer.hand)
        self.k_play(player_screen, player_hand)
        
        self.add_widget(dealer_screen)
        self.add_widget(player_screen)
        
        print(playercards)
        player_hand.delete()
        print(playercards)
        player_hand.deal()
        print(playercards)
        
        self.on_playercards()
        
    def k_play(self, screen, hand):
        screen.clear_widgets()
        for i in hand.cards:
            screen.add_widget(i.image)
    
    def on_playercards(self, *args):
        self.k_play(player_screen, player_hand)
        print(playercards)
        print(args)

class ButtonStrip(BoxLayout):
       def hit(self):
        player_hand.deal()
    
class InfoStrip(BoxLayout):
    pass

class Outer(BoxLayout):
    pass

"""
class PointLabel(Label):
    pass

class ScoreLabel(Label):
    pass
"""

class Screen(BoxLayout):
    def __init__ (self, **kwargs):
        super().__init__(**kwargs)


        
        
        """             

                infostrip = InfoStrip()
                outer = Outer()
                pa = PlayArea()
                buttons = ButtonStrip()
        """


        
"""
        pa.add_widget(dealer_screen)
        pa.add_widget(player_screen)
        outer.add_widget(infostrip)
        outer.add_widget(pa)
        self.add_widget(outer)
        self.add_widget(buttons)
"""
               

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


