
import random
import itertools

SUITS = ['♠', '♥', '♦', '♣']
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
        if len(self.cards) == 0:
            self.deal()
       
    def get_value(self):
        value = 0
        soft_value = 0
        if self.is_blackjack() and not self.split:
            return 'BlackJack'
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
        #shoe needs to be an instance of Shoe  
        self.cards.append(shoe.contents.pop())

    def set_played(self):
        self.played = True
        return

    def set_doubled(self):
        self.doubled = True
        return

    def set_split(self):
        self.split = True
        return
    
    def __repr__(self):
        return str(self.cards)
    

class Dealer:
    def __init__(self):
        dealer_hand = Hand()
        self.hand = dealer_hand

    def play(self):
        if player_hand.is_blackjack():
            for card in itertools.chain(FACES, 'A'):
                if card in self.hand.get_ranks():
                    self.hand.deal()
                    if self.hand.is_blackjack:
                        return 'BlackJack'
                    return
            return
        if player_hand.is_bust:
            if player.insurance:
                self.hand.deal()
            return
        while not self.hand.is_bust:
            if self.hand.get_value() < 17:
                self.hand.deal()
                if self.hand.get_value() == 'BlackJack':
                    return
            else:
                break

class Player:
    def __init__(self, cash=1000, hands=None, bet=25):
        self.cash = cash
        self.bet = bet
        self.result = 0
        self.insurance = False
        if hands is None:
            self.hands = []
        else:
            self.hands = hands

    def play_all_hands(self):
        for hand in self.hands:
            if hand.played:
                continue
            else:
                hand.deal()
                print('\nYOUR SPLIT HANDS:', player.hands)
                self.play(hand)
            
    def play(self, hand):
        self.bet = min(self.bet, self.cash)
        if hand.played:
            return
        self.cash -= self.bet
        print()
        print('YOUR CASH AFTER BET: {0:,}; BET ON THIS HAND: {1} '.format(self.cash, \
                                            hand.bet).center(80, '-'))
        show_hands(hand, dealer.hand)
        if 'A' in dealer.hand.get_ranks():
            if not player.insurance:
                while True:
                    response = input('Insurance? (Y/N)').upper()
                    if response == 'Y':
                        player.set_insurance()
                        self.cash -= 0.5 * self.bet
                        print('Insurance purchased'.center(80))
                        break
                    elif response == 'N':
                        break    
        if hand.is_blackjack():
            hand.set_played()
            return 'BlackJack'
        else:
            if hand.doubled:
                return
            while not hand.is_bust:
                if hand.get_value() == 21:
                    hand.set_played()
                    print()
                    return
                options = ['(H)it', '(S)tand']
                if len(hand.cards) == 2:
                    options.append('(D)ouble')
                    if hand.get_ranks()[0] == hand.get_ranks()[1]:
                        options.append('s(P)lit')
                    elif hand.get_ranks()[0] in FACES \
                         and hand.get_ranks()[1] in FACES:
                        options.append('s(P)lit')
                play = input(str(options).center(79)).upper()
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

    def hit(self, hand):
        hand.deal()
        self.show_hand_in_play(hand)
        
    def stand(self, hand):
        pass

    def double(self, hand):
        self.cash -= self.bet
        hand.deal()
        hand.set_doubled()
        hand.bet *= 2

    def split(self, hand):
        index = self.hands.index(hand)
        self.hands.remove(hand)
        i = 0
        for card in hand.cards:
            split_hand = Hand(card, self.bet)
            split_hand.set_split()
            self.hands.insert(index + i, split_hand)
            i += 1
        self.play_all_hands()  

    def show_hand_in_play(self, hand):
        show_hands(hand, dealer.hand)

    def set_insurance(self):
        self.insurance = True
        return

def show_hands(player, dealer):
    show_dealer_hand(dealer)
    show_player_hand(player)
    print()

def show_dealer_hand(dealer):
    dealer_string = 'Dealer hand:' + str(dealer) + str(dealer.get_value())
    print('{:<40}'.format(dealer_string), end='')

def show_player_hand(player, indented=False):
    if indented:
        print('{:<40}'.format(''), end='')
    player_string = 'Player hand: ' + str(player) + str(player.get_value())
    print('{:<40}'.format(player_string), end='')

def evaluate(pl_hand, dl_hand):
    if pl_hand.get_value() == 'BlackJack':
        if dl_hand.get_value() == 'BlackJack':
            player.result = 1
            return '---PUSH---'
        player.result = 2.5
        return '---YOU HAVE BLACKJACK---'
    elif dl_hand.get_value() == 'BlackJack':
        player.result = 0
        return '---DEALER HAS BLACKJACK---'
    if pl_hand.is_bust:
        player.result = 0
        return '---YOU BUST---'
    elif dl_hand.is_bust:
        player.result = 2
        return '---DEALER BUST---'
    elif pl_hand.get_value() > dl_hand.get_value():
        player.result = 2
        return '---YOU WIN---'
    elif pl_hand.get_value() == dl_hand.get_value():
        player.result = 1
        return '---PUSH---'
    player.result = 0
    return '---YOU LOSE---'

def insurance_payout():
    if dealer.hand.is_blackjack():
        return 1
    return 0
             
if __name__ == '__main__':
    shoe = Shoe()
    player = Player()
    while True:
        if len(shoe.contents) <= shoe.cut_card:
            print('\n!!!SHUFFLE!!!\n')
            shoe = Shoe()

        if player.cash < player.bet:
            print()
            print("YOU LOST ALL YOUR MONEY. YOU MAKE ME SICK YOU STUPID FUCK!!!")
            break
        player_hand = Hand(bet=player.bet)
        dealer = Dealer()
        player_hand.deal()
        player.hands.append(player_hand)
        player.play(player_hand)
        dealer.play()
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
        





        
              


        
        
    
