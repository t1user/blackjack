from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from blackjack import *

class CardView(BoxLayout):
    pass

class PlayArea(BoxLayout):
    pass

class ButtonStrip(BoxLayout):
    pass
    
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

        shoe = Shoe()
        player = Player()
        self.player_hand = Hand(bet=5, shoe=shoe)
        dealer = Dealer(shoe=shoe)
        self.player_hand.deal()
        player.hands.append(self.player_hand)
              
        dealer_screen = CardView()
        player_screen = CardView()
        infostrip = InfoStrip()
        outer = Outer()
        pa = PlayArea()
        buttons = ButtonStrip()

        self.k_play(dealer_screen, dealer.hand)
        self.k_play(player_screen, self.player_hand)
        
        pa.add_widget(dealer_screen)
        pa.add_widget(player_screen)
        outer.add_widget(infostrip)
        outer.add_widget(pa)
        self.add_widget(outer)
        self.add_widget(buttons)
               
    def k_play(self, screen, hand):
        for i in hand.cards:
            screen.add_widget(i.image)
        return
    
    def hit():
        self.player_hand.deal()

class BjApp(App):
    def build(self):
        return Screen()

if __name__ == '__main__':
    BjApp().run()
