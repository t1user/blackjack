
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
        deck = []
        for suit in SUITS:
            for rank in RANKS:
                card = Card(rank, suit) 
                deck.append(card)
        self.contents = []
        for i in range(6):
            for n in deck:
             self.contents.append(n)      
        self.shuffle()
        
    def shuffle(self):
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

    def __repr__(self):
        return str(self.cards)

class Dealer:
    def __init__(self, **kwargs):
        if 'shoe' in kwargs.keys():
            self.shoe = kwargs['shoe']
            self.hand = Hand(shoe=self.shoe)
        else:
            self.hand = Hand()
        
    def play(self, player_hand, **kwargs):
        if player_hand.is_blackjack():
            for card in itertools.chain(FACES, 'A'):
                if card in self.hand.get_ranks():
                    self.hand.deal()
                    if self.hand.is_blackjack:
                        return 'BJ'
                    return
            return
        if player_hand.is_bust:
            if player.insurance:
                self.hand.deal()
            return
        while not self.hand.is_bust:
            if self.hand.get_value() < 17:
                self.hand.deal()
                if self.hand.get_value() == 'BJ':
                    return
            else:
                break

class Player:
    def __init__(self, cash=5000, hands=None, bet=50):
        self.cash = cash
        self.bet = bet
        self.result = 0
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
    
    def run(self):
        if len(self.shoe.contents) <= self.shoe.cut_card:
            print('\n!!!SHUFFLE!!!\n')
            self.shoe = Shoe()

#        if player.cash < player.bet:
#            print()
#            print("YOU LOST ALL YOUR MONEY. YOU MAKE ME SICK YOU STUPID FUCK!!!")
#            break
        self.player.hands = []
        print('hands cleared')
        self.player_hand = Hand(bet=self.player.bet)
        self.dealer = Dealer()
        self.player_hand.deal()
        self.player.hands.append(self.player_hand)
        self.play(self.player_hand)
        self.insurance_asked = False

    def play(self, hand):
        print('play', hand)
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
        """
        else:
            if hand.doubled :
                return
            self.player_input(hand)
        """
        
    def player_input(self, hand):
        if hand.get_value() == 21:
            hand.played = True
        elif hand.is_bust:
            hand.played = True
            return
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
                return
            else:
                print('running dealer')
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
            
            """
            self.player_hand = hand
            if self.player_hand.played:
                continue
            else:
                print('playing hand: ', self.player_hand)
                self.player_hand.deal()
                self.play(self.player_hand)
            """

    def split(self, hand):
        index = self.player.hands.index(hand)
        self.player.hands.remove(hand)
        i = 0
        for card in hand.cards:
            split_hand = Hand(card, self.player.bet)
            split_hand.split = True
            self.player.hands.insert(index + i, split_hand)
            i += 1
        self.play_all_hands()  
             
    def hit(self, hand):
        hand.deal()
        
    def stand(self, hand):
        hand.played = True

    def double(self, hand):
        self.player.cash -= self.player.bet
        hand.deal()
        hand.doubled = True
        hand.played = True
        hand.bet *= 2
 
    def final(self):
        print('entering final')
        for hand in self.player.hands:
            hand.result_message = self.evaluate(hand, self.dealer.hand)
            self.player.cash += self.result * hand.bet
        if self.player.insurance:
            self.player.cash = self.insurance_payout() * self.player.bet
            self.player.insurance = False
        print('round finished')

        
    def evaluate(self, pl_hand, dl_hand):
        if pl_hand.get_value() == 'BJ':
            if dl_hand.get_value() == 'BJ':
                self.result = 1
                return '---PUSH---'
            self.result = 2.5
            return '---YOU HAVE BLACKJACK---'
        elif dl_hand.get_value() == 'BJ':
            self.result = 0
            return '---DEALER HAS BLACKJACK---'
        if pl_hand.is_bust:
            self.player.result = 0
            return "---YOU'RE BUST---"
        elif dl_hand.is_bust:
            self.result = 2
            return '---DEALER BUST---'
        elif pl_hand.get_value() > dl_hand.get_value():
            self.result = 2
            return '---YOU WIN---'
        elif pl_hand.get_value() == dl_hand.get_value():
            self.result = 1
            return '---PUSH---'
        self.result = 0
        return '---YOU LOSE---'

    def insurance_payout(self):
        self.insurance_asked = False
        if self.dealer.hand.is_blackjack():
            return 1
        return 0 



"""
                if play == 'H':
                    self.hit(hand)
                if play == 'S':
                    self.stand(hand)
                    hand.set_played()
                    return
                if 's(P)lit' in options:
                    if play == 'P':
                        if self.cash < self.bet:
                            print("YOU DON'T HAVE ENOUGH CASH TO SPLIT!!!".center(80))
                            continue
                        self.split(hand)
                        return
                if '(D)ouble' in options:
                    if play == 'D':
                        if self.cash < self.bet:
                            print("YOU DON'T HAVE ENOUGH CASH TO DOUBLE!!!".center(80))
                            continue
                        self.double(hand)
                        hand.set_played()
                        return
            return
"""
        
"""        
        print()
        print('RESULT:'.center(80))
        show_dealer_hand(dealer.hand)
        counter = 0
        for hand in player.hands:
            if counter > 0:
                show_player_hand(hand, True)
            else:
                show_player_hand(hand)
            result = evaluate(hand, dealer.hand)
            cash_result = player.result * hand.bet
            print('{} hand cash result: {:+}'.format(result, \
                    cash_result - hand.bet).center(80))
            player.cash += cash_result
            counter += 1
        if player.insurance:
            cash_result = insurance_payout() * player.bet
            print('---Insurance: cash result: {:+}'.format(cash_result - player.bet/2)
                  .center(80))
            player.cash += cash_result
            player.insurance = False
        player.hands = []
"""

if __name__ == '__main__':
    pass

        





        
              


        
        
    
