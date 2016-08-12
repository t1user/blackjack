from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from blackjack import *

class Screen_1(BoxLayout):
    orientation = 'vertical'
    def __init__ (self, **kwargs):
        super().__init__(**kwargs)
        dealer_screen = BoxLayout()
        player_screen = BoxLayout()


        #define_shoe()
        shoe = Shoe()
        #define_player()
        player = Player()
        player_hand = Hand(bet=5, shoe=shoe)
        #define_dealer()
        dealer = Dealer(shoe=shoe)
        player_hand.deal()
        player.hands.append(player_hand)
        #player.play(player_hand, dealer=dealer)
        #dealer.play()

        
        dealer_screen.add_widget(self.k_play(dealer.hand))        
        player_screen.add_widget(self.k_play(player_hand))

        self.add_widget(dealer_screen)
        self.add_widget(player_screen)	
       

               
    def k_play(self, hand):
        x = FloatLayout()
        for i in hand.cards:
            x.add_widget(i.image)
        return x




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


class BlackjackApp(App):
    def build(self):
        return Screen_1()


if __name__ == '__main__':
    BlackjackApp().run()
