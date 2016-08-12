from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from blackjack import *
from kivy.properties import StringProperty

class Screen(BoxLayout):
    file = StringProperty()
    file1 = StringProperty()
    def __init__ (self, **kwargs):
        super(Screen, self).__init__(**kwargs)
        self.shoe = Shoe()  
    def show_card(self):
        c = self.shoe.contents.pop()
        self.file1 = self.file
        self.file = './Cards/'+c.rank.lower()+'_'+c.suit.lower()+'.png'
       
   
"""    
       
       
        l = ScatterLayout()
        s = Scatter
        c = shoe.contents.pop()
        s.add_widget(c.image)
        l.add_widget(s)
        #l.add_widget(shoe.contents.pop().image)
        #l.add_widget(shoe.contents.pop().image)
        self.add_widget(l)



        #dealer_screen = BoxLayout()
        #player_screen = BoxLayout()


        #define_shoe()
 
        #define_player()
        player = Player()
        player_hand = Hand(bet=5, shoe=shoe)
        #define_dealer()
        dealer = Dealer(shoe=shoe)
        player_hand.deal()
        player.hands.append(player_hand)
        #player.play(player_hand, dealer=dealer)
        #dealer.play()

        
        #dealer_screen.add_widget(self.k_play(dealer.hand))        
        #player_screen.add_widget(self.k_play(player_hand))

        #self.add_widget(dealer_screen)
        #self.add_widget(player_screen)	
        
        #print(dealer.hand)
        #print(player_hand)
         
         
               
    def k_play(self, hand):
        x = ScatterLayout()
        for i in hand.cards:
            x.add_widget(i.image)
            print('Added: ', i)
        return x




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
        return Screen()


if __name__ == '__main__':
    BlackjackApp().run()

