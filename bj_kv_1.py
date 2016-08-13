from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from blackjack import *

class CardView(BoxLayout):
    pass

class PlayArea(BoxLayout):
    pass

class Screen(BoxLayout):
    orientation = 'vertical'
    def __init__ (self, **kwargs):
        super().__init__(**kwargs)
        dealer_screen = BoxLayout()
        player_screen = BoxLayout()


        shoe = Shoe()
        player = Player()
        player_hand = Hand(bet=5, shoe=shoe)
        dealer = Dealer(shoe=shoe)
        player_hand.deal()
        player.hands.append(player_hand)
        dealer_screen = CardView()
        player_screen = CardView()
        pa = PlayArea()

        self.k_play(dealer_screen, dealer.hand)
        self.k_play(player_screen, player_hand)
        
        #dealer_screen.add_widget(self.k_play(dealer.hand))        
        #player_screen.add_widget(self.k_play(player_hand))

        pa.add_widget(dealer_screen)
        pa.add_widget(player_screen)	
        self.add_widget(pa)
       

               
    def k_play(self, screen, hand):
        for i in hand.cards:
            screen.add_widget(i.image)
        return




"""
		for i in shoe.contents:
			x = Scatter()
			y = Image(source='./Cards/'+i.rank.lower()+'_'+i.suit.lower()+'.png')
			x.add_widget(y)
			self.add_widget(x)

		shoe=blackjack.Shoe()
		for c in shoe.contents:
			self.add_widget(Image(source='./Cards/'+c.rank.lower()+'_'+c.suit.lower()+'.png'))
"""


class BjApp(App):
    def build(self):
        return Screen()


if __name__ == '__main__':
    BjApp().run()
