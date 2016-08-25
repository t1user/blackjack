
import random
import itertools

SUITS = ['S', 'H', 'D', 'C']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
FACES = ['10', 'J', 'Q', 'K']

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return self.rank + self.suit


class Shoe:
    def __init__(self):
        self.shuffle()
        
    def shuffle(self):        
        self.will_shuffle = ''
        deck = []
        for suit in SUITS:
            for rank in RANKS:
                card = Card(rank, suit) 
                deck.append(card)
        self.contents = []
        for i in range(6):
            for n in deck:
             self.contents.append(n)      

        random.shuffle(self.contents)
        self.cut_card = round(random.randint(20,25)*len(self.contents)/100,0)


class Hand:
    def __init__(self, cards=None, bet=0):
        self.shoe = shoe
        if cards is None:
            self.cards = []
        else:
            self.cards = []
            self.cards.append(cards)
        self.is_bust = False
        self.played = False
        self.doubled = False
        self.split = False
        self.bet = bet
        self.result_message = ''
        self.result = 0
        if len(self.cards) == 0:
            self.deal()
       
    def get_value(self):
        value = 0
        soft_value = 0
        if self.is_blackjack() and not self.split:
            return 'BJ'
        for card in self.cards:
            if card.rank in FACES:
                card_value = 10
            elif card.rank == 'A':
                card_value = 1
                soft_value = 10
            else:
                card_value = int(card.rank)
            value += card_value
        if value <= 11:
            value += soft_value
        if value > 21:
            self.is_bust = True
        return value

    def get_ranks(self):
        ranks = []
        for card in self.cards:
            ranks.append(card.rank)
        return ranks
    
    def is_blackjack(self):
        if len(self.cards) != 2:
            return False
        if 'A' in self.get_ranks():
            for i in FACES:
                if i in self.get_ranks():
                    return True
        return False

    def deal(self):
        self.cards.append(self.shoe.contents.pop())
        if len(self.shoe.contents) < self.shoe.cut_card:
            self.shoe.will_shuffle = 'SHUFFLE'

    def __repr__(self):
        return str(self.cards)


class Dealer:
    def __init__(self):
        self.hand = Hand()
        
    def play(self, player_hand, player):
        if player_hand.is_blackjack():
            for card in itertools.chain(FACES, 'A'):
                if card in self.hand.get_ranks():
                    self.hand.deal()
                    if self.hand.is_blackjack:
                        return 'BJ'
                    return
            return
        
        # if at least one hand is not bust dealer should take a card
        # dealer should also take a card if insurance is in play
        for hand in player.hands:
            if hand.is_bust:
                if player.insurance:
                    #take just one card to check for bj
                    self.hand.deal()
                    # return gives control back to the controller
                    # so no extra cards are taken (just one)
                    # case: hand bust, insurance in play
                    return
                # continue to look for a non-bust hand
                continue
            # break stops 'for' loop because a non-bust hand has been found
            break
        # we reached this point either because all cards are bust
        # or because we found a non-bust card and got broken out of 'for'
        # if it's the first case return control to the controller
        # dealer hand not played
        # otherwise move on to play dealer hand
        if hand.is_bust:
            return
        
        # we should be at this point if dealer hand needs to be played    
        while not self.hand.is_bust:
            if self.hand.get_value() < 17:
                self.hand.deal()
                if self.hand.get_value() == 'BJ':
                    return
            else:
                break


class Player:
    def __init__(self, cash=500, hands=None, bet=50):
        self.cash = cash
        self.bet = bet
        self.insurance = False
        if hands is None:
            self.hands = []
        else:
            self.hands = hands


class Controller:  
    def __init__(self):
        self.shoe = Shoe()
        global shoe
        shoe = self.shoe
        self.player = Player()
        self.insurance_option = False
        self.insurance_asked = False
        self.no_cash = False
    
    def run(self):
        if len(shoe.contents) <= shoe.cut_card:
            shoe.shuffle()
        if self.player.cash < self.player.bet:
            self.no_cash = True
            return
        self.player.hands = []
        self.player_hand = Hand(bet=self.player.bet)
        self.dealer = Dealer()
        self.player_hand.deal()
        self.player.hands.append(self.player_hand)
        self.play(self.player_hand)
        self.insurance_asked = False

    def play(self, hand):
        self.bet = min(self.player.bet, self.player.cash)
        if hand.played:
            return
        self.player.cash -= self.bet
        if 'A' in self.dealer.hand.get_ranks():
            if not self.player.insurance and not self.insurance_asked:
                self.insurance_option = True   
        if hand.is_blackjack():
            hand.played = True
            return 'BJ'
        
    def player_input(self, hand):
        if hand.get_value() == 21:
            hand.played = True
        elif hand.is_bust:
            hand.played = True
        elif not hand.played:
            self.options = [1, 0, 0, 1]
            if len(hand.cards) == 2:
                self.options = [1, 0, 1, 1]
                if hand.get_ranks()[0] == hand.get_ranks()[1]:
                    self.options = [1, 1, 1, 1]
                elif hand.get_ranks()[0] in FACES \
                     and hand.get_ranks()[1] in FACES:
                    self.options = [1, 1, 1, 1]

        for hand in self.player.hands:
            if not hand.played:
                self.player_hand = hand
                if len(self.player_hand.cards) < 2:
                    self.player_hand.deal()
                    # need to check if 21 before waiting for user input
                    self.player_input(self.player_hand)
                return
            
        self.dealer.play(self.player_hand, player=self.player)
        self.final()
    
    def buy_insurance(self):
        self.player.insurance = True
        self.player.cash -= 0.5 * self.bet
        self.insurance_option = False
        self.insurance_asked = True

    def decline_insurance(self):
        self.player.insurance = False
        self.insurance_asked = True
        self.insurance_option = False
    
    def play_all_hands(self):
        for hand in self.player.hands:
            self.play(hand)

    def split(self, hand):
        if self.player.cash < self.player.bet:
            self.no_cash = True
            return        
        index = self.player.hands.index(hand)
        self.player.hands.remove(hand)
        i = 0
        for card in hand.cards:
            split_hand = Hand(card, self.player.bet)
            split_hand.split = True
            self.player.hands.insert(index + i, split_hand)
            i += 1
        # bet is charged while playing every new hand 
        # so add-back original bet to keep total bet at 2x
        self.player.cash += self.player.bet 
        self.play_all_hands()  
             
    def hit(self, hand):
        hand.deal()
        
    def stand(self, hand):
        hand.played = True

    def double(self, hand):
        if self.player.cash < self.player.bet:
            self.no_cash = True
            return
        self.player.cash -= self.player.bet
        hand.deal()
        hand.doubled = True
        hand.played = True
        hand.bet *= 2
 
    def final(self):
        for hand in self.player.hands:
            hand.result_message = self.evaluate(hand, self.dealer.hand)
            self.player.cash += hand.result * hand.bet
        if self.player.insurance:
            self.player.cash += self.insurance_payout()*1.5*self.player.bet
            self.player.insurance = False
        
    def evaluate(self, pl_hand, dl_hand):
        if pl_hand.get_value() == 'BJ':
            if dl_hand.get_value() == 'BJ':
                pl_hand.result = 1
                return 'PUSH'
            pl_hand.result = 2.5
            return 'YOU HAVE BLACKJACK'
        elif dl_hand.get_value() == 'BJ':
            pl_hand.result = 0
            return 'DEALER HAS BLACKJACK'
        if pl_hand.is_bust:
            pl_hand.result = 0
            return "YOU'RE BUST"
        elif dl_hand.is_bust:
            pl_hand.result = 2
            return 'DEALER BUST'
        elif pl_hand.get_value() > dl_hand.get_value():
            pl_hand.result = 2
            return 'YOU WIN'
        elif pl_hand.get_value() == dl_hand.get_value():
            pl_hand.result = 1
            return 'PUSH'
        pl_hand.result = 0
        return 'YOU LOSE'

    def insurance_payout(self):
        self.insurance_asked = False
        if self.dealer.hand.is_blackjack():
            return 1
        return 0 

        
              


        
        
    
