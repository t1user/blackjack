#!/usr/local/bin/python3

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.properties import ListProperty, ObjectProperty, NumericProperty

from blackjack import *

from copy import deepcopy

class CardView(RelativeLayout):
    pass

class PointsLabel(Label):
    pass

class PlayActionButtons(BoxLayout):
    def hit(self):
        a = player.hands.pop()
        a.deal()
        player.hands.append(a)        
        s.playerhands = deepcopy(player.hands)
    
    def double(self):
        dealer.hand.deal()
        s.dealercards = dealer.hand.cards
    
    def split(self):
        index = player.hands.index(player_hand)
        player.hands.remove(player_hand)
        i = 0
        for card in player_hand.cards:
            split_hand = Hand(card, 5, shoe=shoe)
            #split_hand.set_split()
            player.hands.insert(index + i, split_hand)
            i += 1
        s.playerhands = deepcopy(player.hands)
    
class Screen(BoxLayout):
    
    playerhands = ListProperty()
    dealercards = ListProperty()
    player_screen = ObjectProperty()
    dealer_screen = ObjectProperty()
    buttonstrip = ObjectProperty()
    
    pos_para = NumericProperty(.4)
    pos_para_dealer = NumericProperty(.4)
    hand_spacing = NumericProperty(100)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.playerhands = player.hands
        self.dealercards = dealer.hand.cards
        
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
        self.hand_spacing = max(100 - max(len(self.playerhands)-3, 0)
         * 50, 20)
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
        return screen
        
    def on_dealercards(self, *args):
        self.x_card_offset = 35
        self.y_card_offset = 0
        if len(dealer.hand.cards) > 6:
            self.pos_para_dealer = 0.2
        self.k_play(self.dealer_screen, dealer.hand)
         
         
class Bj5App(App):
    def build(self):
        global s
        s = Screen()
        return s
        
        
if __name__ == '__main__':
    shoe = Shoe()
    player = Player()
    player_hand = Hand(bet=5, shoe=shoe)
    dealer = Dealer(shoe=shoe)
    player_hand.deal()
    player.hands.append(player_hand)
    
    Bj5App().run()


