import pytest

from blackjack.engine import (
    DECK,
    Card,
    Dealer,
    GameError,
    GameStrategy,
    Hand,
    HandPlay,
    NotEnoughCash,
    PlayDecision,
    Player,
    Shoe,
    State,
)
from blackjack.strategies import FixedBettingStrategy, RandomStrategy


def test_Card_cannot_be_instantiated_with_wrong_suit():
    with pytest.raises(ValueError):
        Card("K", "A")


def test_Card_cannot_be_instantiated_with_wrong_rank():
    with pytest.raises(ValueError):
        Card("11", "D")


def test_ace_value():
    ace_card = Card("A", "H")
    assert ace_card.value == 1


def test_ace_soft_value():
    ace_card = Card("A", "D")
    assert ace_card.soft_value == 11


def test_king_is_a_ten():
    king_card = Card("K", "H")
    assert king_card.value == 10


def test_ten_soft_value():
    assert Card("10", "H").soft_value == 10


def test_non_face_correct_value():
    assert Card("2", "H").value == 2


def test_non_face_correct_soft_value():
    assert Card("7", "D").soft_value == 7


def test_equal_value_cards():
    assert Card("K", "D") == Card("Q", "H")


def test_card_str():
    assert str(Card("K", "H")) == "K♥"


def test_card_repr():
    assert repr(Card("K", "H")) == "Card(rank='K', suit='H')"


def test_deck_correct_number_of_cards():
    assert len(DECK) == 52


def test_new_shoe_has_correct_number_of_cards():
    shoe = Shoe(6)
    assert len(shoe) == 6 * 52


def test_shoe_has_correct_number_of_cards_after_shuffling():
    shoe = Shoe(6)
    shoe.shuffle()
    assert len(shoe) == 6 * 52


def test_shoe_has_correct_number_of_cards_after_shuffling_1():
    shoe = Shoe(6)
    while not shoe.will_shuffle:
        shoe.deal()
    shoe.shuffle()
    assert len(shoe) == 6 * 52


def test_shoe_hi_lo_count():
    shoe = Shoe(6)
    card = shoe.deal()
    assert shoe.hilo_count == card.hilo_count


def test_shoe_emits_event_on_new_card():
    shoe = Shoe(6)

    class Hitter:
        count = 0

        def hit(self, *args):
            self.count += 1

    h = Hitter()
    shoe.newCardEvent += h.hit

    shoe.deal()

    assert h.count == 1


def test_shoe_newCardEvent_emits_card():
    shoe = Shoe(6)

    class Hitter:
        last_card = None

        def hit(self, card):
            self.last_card = card

    h = Hitter()
    shoe.newCardEvent += h.hit

    shoe.deal()

    assert isinstance(h.last_card, Card)


def test_empty_hand_has_value_zero():
    assert Hand().value == 0


@pytest.fixture
def two_card_hand() -> Hand:
    return Hand(Card("5", "D"), Card("9", "H"))


def test_hand_value(two_card_hand: Hand):
    assert two_card_hand.value == 14


def test_hand_hard_value(two_card_hand: Hand):
    assert two_card_hand.hard_value == 14


def test_hand_soft_value(two_card_hand: Hand):
    assert two_card_hand.soft_value == 14


def test_hand_cannot_split(two_card_hand: Hand):
    assert not two_card_hand.can_split()


def test_hand_is_not_blackjack(two_card_hand: Hand):
    assert not two_card_hand.is_blackjack()


def test_blackjack_is_blackjack():
    assert Hand(Card("A", "H"), Card("K", "D")).is_blackjack()


def test_blackjack_cannot_split():
    assert not Hand(Card("A", "H"), Card("K", "D")).can_split()


def test_hand_with_ace_value():
    # It's (10/20) so if no more cards taken the value that matters is 20
    assert Hand(Card("A", "D"), Card("9", "H")).value == 20


def test_hand_with_ace_value_1():
    assert Hand(Card("A", "D"), Card("9", "H"), Card("8", "C")).value == 18


def test_hand_with_ace_value_2():
    assert Hand(Card("2", "S"), Card("A", "C"), Card("J", "C")).value == 13


def test_hand_with_ace_hard_value():
    assert Hand(Card("A", "D"), Card("9", "H")).hard_value == 10


def test_hand_with_ace_soft_value():
    assert Hand(Card("A", "D"), Card("9", "H")).soft_value == 20


def test_double_aces_is_12():
    assert Hand(Card("A", "D"), Card("A", "H")).value == 12


def test_double_aces_not_bust():
    assert not Hand(Card("A", "D"), Card("A", "H")).is_bust()


def test_hand_with_multiple_aces_value():
    assert (
        Hand(
            Card("A", "D"),
            Card("A", "H"),
            Card("A", "S"),
            Card("A", "C"),
            Card("3", "C"),
        ).value
        == 17
    )


def test_hand_with_multiple_aces_soft_value():
    assert (
        Hand(
            Card("A", "D"),
            Card("A", "H"),
            Card("A", "S"),
            Card("A", "C"),
            Card("3", "C"),
        ).soft_value
        == 17
    )


def test_hand_with_multiple_aces_hard_value():
    assert (
        Hand(
            Card("A", "D"),
            Card("A", "H"),
            Card("A", "S"),
            Card("A", "C"),
            Card("3", "C"),
        ).hard_value
        == 7
    )


def test_not_bust_with_ace():
    # soft value is bust but hard not
    assert not Hand(Card("A", "D"), Card("9", "H"), Card("8", "C")).is_bust()


def test_bust_with_ace():
    # both soft and hard values are bust
    assert Hand(
        Card("A", "D"), Card("9", "H"), Card("8", "C"), Card("10", "D")
    ).is_bust()


def test_can_split_double_aces():
    assert Hand(Card("A", "D"), Card("A", "H")).can_split()


def test_Hand_eq():
    hand1 = Hand(Card("A", "D"), Card("9", "H"), Card("5", "C"))
    hand2 = Hand(Card("10", "H"), Card("5", "D"))
    assert hand1 == hand2


def test_Hand_not_eq():
    hand1 = Hand(Card("A", "D"), Card("9", "H"), Card("4", "C"))
    hand2 = Hand(Card("10", "H"), Card("5", "D"))
    assert hand1 != hand2


def test_Hand_gt():
    hand1 = Hand(Card("A", "D"), Card("9", "H"), Card("8", "C"))
    hand2 = Hand(Card("10", "H"), Card("5", "D"))
    assert hand1 > hand2


def test_Hand_lt():
    hand1 = Hand(Card("A", "D"), Card("9", "H"), Card("8", "C"))
    hand2 = Hand(Card("10", "H"), Card("5", "D"))
    assert hand2 < hand1


def test_busted_hand_smaller_than_non_busted_hand():
    hand1 = Hand(Card("A", "D"), Card("9", "H"), Card("8", "C"), Card("10", "C"))
    hand2 = Hand(Card("10", "H"), Card("5", "D"))
    assert hand2 > hand1


def test_two_busted_hands_equal():
    hand1 = Hand(Card("A", "D"), Card("9", "H"), Card("8", "C"), Card("10", "C"))
    hand2 = Hand(Card("10", "H"), Card("5", "D"), Card("9", "H"))
    assert hand1 == hand2


def test_Hand_gets_new_card():
    hand = Hand()
    card = Card("A", "D")
    hand += card
    assert card in hand
    assert len(hand) == 1


def test_blackjack_trumps_21():
    hand_bj = Hand(Card("A", "S"), Card("K", "D"))
    hand_21 = Hand(Card("10", "D"), Card("5", "H"), Card("6", "D"))
    assert hand_bj > hand_21


def test_21_less_than_blackjack():
    # testing if comparison operators work on both sides
    hand_bj = Hand(Card("A", "S"), Card("K", "D"))
    hand_21 = Hand(Card("10", "D"), Card("5", "H"), Card("6", "D"))
    assert hand_21 < hand_bj


def test_two_blackjacks_equal():
    hand_1 = Hand(Card("A", "S"), Card("K", "D"))
    hand_2 = Hand(Card("A", "D"), Card("J", "S"))
    assert hand_1 == hand_2


class TestDealer:

    def test_dealer_deals_card(self):
        dealer = Dealer()
        hand = Hand()
        dealer.deal(hand)
        assert len(hand) == 1

    def test_dealer_deals_self(self):
        dealer = Dealer()
        dealer.deal_self()
        assert len(dealer.hand) == 1

    def test_dealer_doesn_shuffle_when_not_necessary(self):
        dealer = Dealer()
        shoe = dealer.shoe.copy()
        dealer.shuffle()
        assert dealer.shoe == shoe

    def test_shuffle_doesnt_leave_dealer_cards(self):
        dealer = Dealer()
        dealer.deal_self()
        dealer.deal_self()
        dealer.shuffle()
        assert len(dealer.hand) == 0

    def test_dealer_force_shuffle(self):
        dealer = Dealer()
        shoe = dealer.shoe.copy()
        dealer.force_shuffle()
        assert dealer.shoe != shoe

    def test_hilo_updated_after_dealer_deals(self):
        dealer = Dealer()
        hand = Hand()
        dealer.deal(hand)
        assert dealer.shoe.hilo_count == hand[0].hilo_count

    def test_hilo_updated_after_dealer_deals_self(self):
        dealer = Dealer()
        dealer.deal_self()
        assert dealer.shoe.hilo_count == dealer.hand[0].hilo_count

    def test_dealer_has_ace_raises_on_empty_hand(self):
        dealer = Dealer()
        with pytest.raises(GameError):
            dealer.has_ace

    def test_dealer_has_ace_with_ace(self):
        dealer = Dealer()
        dealer.hand += Card("A", "H")
        assert dealer.has_ace

    def test_dealer_has_ace_with_no_ace(self):
        dealer = Dealer()
        dealer.hand += Card("9", "H")
        assert not dealer.has_ace

    def test_Dealer_in_dealer_repr(self):
        assert "Dealer" in repr(Dealer())

    def test_dealer_repr_reports_card_in_hand(self):
        dealer = Dealer()
        card = Card("A", "H")
        dealer.hand += card
        assert str(card) in repr(dealer)


class TestPlayer:

    @pytest.fixture
    def player(self):
        return Player(RandomStrategy(), FixedBettingStrategy(10), 100)

    def test_cash_credits(self, player: Player):
        player.credit(10)
        assert player.cash == 110

    def test_cash_charges(self, player: Player):
        print(id(player), player)
        player.charge(10)
        assert player.cash == 90

    def test_overdrawn_raises(self, player: Player):
        with pytest.raises(NotEnoughCash):
            player.charge(110)

    def test_overdrawn_doesnt_change_balance(self, player: Player):
        try:
            player.charge(110)
        except NotEnoughCash:
            pass
        assert player.cash == 100


class TestHandPlay:

    @pytest.fixture
    def random_player(self):
        return Player(RandomStrategy(), FixedBettingStrategy(5))

    @pytest.fixture
    def hand_play(self, random_player: Player):
        return HandPlay.from_player(random_player)

    @pytest.fixture
    def dealer(self):
        return Dealer()

    # every PlayDecision is next power of 2:
    # HIT: 1
    # SPLIT: 2
    # DOUBLE: 4
    # STAND: 8
    # SURRENDER: 16
    # value of allowed_choices is the numerical sum of available options

    def test_double_aces_can_split(self, hand_play: HandPlay):
        hand_play += Card("A", "H")
        hand_play += Card("A", "S")
        assert hand_play.allowed_choices.value == 31  # type: ignore

    def test_three_cards_cannot_split_double_or_surrender(self, hand_play: HandPlay):
        hand_play += Card("A", "H")
        hand_play += Card("A", "S")
        hand_play += Card("K", "H")
        assert hand_play.allowed_choices.value == 9  # type: ignore

    def test_non_pair_cannot_split(self, hand_play: HandPlay):
        hand_play += Card("A", "S")
        hand_play += Card("9", "H")
        assert hand_play.allowed_choices.value == 29  # type: ignore

    def test_no_options_if_done(self, hand_play: HandPlay):
        hand_play.done()
        assert hand_play.allowed_choices is None

    # Return value is None if the hand is done or HandPlay/multiple HandPlays otherwise
    def test_hit(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("9", "H")
        cards = hand_play.hand.copy()
        return_value = hand_play.hit(dealer)
        assert len(hand_play.hand) == 3
        assert cards[0] in hand_play.hand
        assert cards[1] in hand_play.hand
        assert isinstance(return_value, HandPlay)

    def test_stand(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("9", "H")
        cards = hand_play.hand.copy()
        return_value = hand_play.stand(dealer)
        assert len(hand_play.hand) == 2
        assert cards[0] in hand_play.hand
        assert cards[1] in hand_play.hand
        assert hand_play.is_done
        assert return_value is State.DONE

    def test_surrender_is_done(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("9", "H")
        hand_play.surrender(dealer)
        assert hand_play.is_done

    def test_surrender_charges_half_bet(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("9", "H")
        betsize = hand_play.betsize
        hand_play.surrender(dealer)
        assert hand_play.result == -0.5 * betsize

    def test_double(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("9", "H")
        cards = hand_play.hand.copy()
        return_value = hand_play.double(dealer)
        assert len(hand_play.hand) == 3
        assert cards[0] in hand_play.hand
        assert cards[1] in hand_play.hand
        assert hand_play.is_done
        assert return_value is State.DONE

    def test_double_charges_player(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("9", "H")
        starting_cash = hand_play.player.cash
        betsize = hand_play.betsize
        hand_play.double(dealer)
        assert hand_play.player.cash + betsize == starting_cash

    def test_split_returns_list_of_two_cards(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("A", "H")
        return_value = hand_play.split(dealer)
        assert isinstance(return_value, list)
        assert len(return_value) == 2

    def test_split_charges_player(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("A", "H")
        starting_cash = hand_play.player.cash
        betsize = hand_play.betsize
        hand_play.split(dealer)
        assert hand_play.player.cash + betsize == starting_cash

    def test_split_returned_first_hand(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("A", "H")
        cards = hand_play.hand.copy()
        return_value = hand_play.split(dealer)
        testing_card = cards[0]
        testing_hand = return_value[0]
        assert isinstance(testing_hand, HandPlay)
        assert len(testing_hand.hand) == 2
        assert testing_card in testing_hand.hand
        assert testing_hand.splits == 1

    def test_split_returned_second_hand(self, hand_play: HandPlay, dealer: Dealer):
        hand_play += Card("A", "S")
        hand_play += Card("A", "H")
        cards = hand_play.hand.copy()
        return_value = hand_play.split(dealer)
        testing_card = cards[1]
        testing_hand = return_value[1]
        assert isinstance(testing_hand, HandPlay)
        assert len(testing_hand.hand) == 2
        assert testing_card in testing_hand.hand
        assert testing_hand.splits == 1

    def test_one_hand_inherits_insurance_after_split(
        self, hand_play: HandPlay, dealer: Dealer
    ):
        hand_play += Card("A", "S")
        hand_play += Card("A", "H")
        hand_play.insurance = 5
        return_value = hand_play.split(dealer)
        assert return_value[0].insurance == 5
        assert return_value[1].insurance == 0

    def test_no_blackjack_after_split(self, hand_play: HandPlay):

        class DeterminedDealer(Dealer):
            def deal(self, hand: Hand | HandPlay):
                hand += Card("K", "S")

        dealer = DeterminedDealer()

        hand_play += Card("A", "S")
        hand_play += Card("A", "H")
        return_value = hand_play.split(dealer)
        test_hand = return_value[0]
        assert not test_hand.hand.is_blackjack()

    def test_eval_dealer_wins(self, hand_play: HandPlay):
        dealer = Dealer(hand=Hand(Card("A", "S"), Card("9", "H")))

        hand_play += Card("8", "S")
        hand_play += Card("9", "H")

        # cash recorded only after original bet charged
        start_cash = hand_play.player.cash
        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        end_cash = hand_play.player.cash
        # player lost so doesn't get any cash back
        assert end_cash == start_cash

    def test_eval_player_wins(self, hand_play: HandPlay):
        dealer = Dealer(hand=Hand(Card("8", "S"), Card("9", "H")))

        hand_play += Card("A", "S")
        hand_play += Card("9", "H")

        # cash recorded only after original bet charged
        start_cash = hand_play.player.cash
        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        end_cash = hand_play.player.cash
        # player won so should cash out 2x bet
        assert end_cash == start_cash + 2 * hand_play.betsize

    def test_eval_push(self, hand_play: HandPlay):
        dealer = Dealer(hand=Hand(Card("10", "S"), Card("K", "H")))

        hand_play += Card("A", "S")
        hand_play += Card("9", "H")

        # cash recorded only after original bet charged
        start_cash = hand_play.player.cash
        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        end_cash = hand_play.player.cash
        # push so player gets back original bet
        assert end_cash == start_cash + hand_play.betsize

    def test_eval_insurance(self, hand_play: HandPlay):

        dealer = Dealer(hand=Hand(Card("A", "S"), Card("K", "H")))

        hand_play += Card("A", "S")
        hand_play += Card("9", "H")
        # insurance is never actually charged to player in this test
        hand_play.insurance = 1
        start_cash = hand_play.player.cash
        # this is won (player not credited yet)
        hand_play.eval_insurance(dealer)
        # this is lost, but it actually settles accounts with player
        # i.e. credits insurance won
        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        # we haven't charged anything in this mock situation
        # full test with charging below
        end_cash = hand_play.player.cash
        # insurance was not charged so final cash is higher than in reality
        assert end_cash == start_cash + hand_play.insurance * 3

    @pytest.fixture
    def always_insuring_player(self):
        class PositiveInsuranceGameStrategy(RandomStrategy):
            def insurance(self, dealer_hand: Hand, player_hand: Hand):
                return True

        return Player(PositiveInsuranceGameStrategy(), FixedBettingStrategy(5))

    def test_insurance_full(self, always_insuring_player: Player):
        player = always_insuring_player
        start_cash = player.cash  # before bet was charged
        hand_play = HandPlay.from_player(player)  # bet charged here
        assert hand_play

        dealer = Dealer(hand=Hand(Card("A", "S"), Card("K", "H")))

        hand_play += Card("A", "S")
        hand_play += Card("9", "H")

        hand_play.play_insurance(dealer)  # insurance charged here
        # this is won
        hand_play.eval_insurance(dealer)
        # this is lost (and accounts are settled)
        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        end_cash = player.cash
        # insurance won compensates hand lost
        assert end_cash == start_cash

    def test_insurance_full_player_blackjack(self, always_insuring_player: Player):
        player = always_insuring_player
        start_cash = player.cash  # before bet was charged

        hand_play = HandPlay.from_player(player)  # bet is charged here
        assert hand_play

        dealer = Dealer(hand=Hand(Card("A", "S"), Card("K", "H")))

        hand_play += Card("A", "S")
        hand_play += Card("J", "H")

        hand_play.play_insurance(dealer)  # insurance is charged here

        # this is won
        hand_play.eval_insurance(dealer)
        # this is lost (and accounts are settled)
        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        end_cash = hand_play.player.cash
        # insurance won compensates hand lost
        assert end_cash == start_cash + hand_play.betsize  # it's even money

    def test_insurance_full_player_blackjack_no_dealer_blackjack(
        self, always_insuring_player: Player
    ):
        player = always_insuring_player
        start_cash = player.cash  # before bet was charged

        hand_play = HandPlay.from_player(player)  # bet is charged here
        assert hand_play

        dealer = Dealer(hand=Hand(Card("A", "S"), Card("9", "H")))

        hand_play += Card("A", "S")
        hand_play += Card("J", "H")

        hand_play.play_insurance(dealer)  # insurance is charged here

        # this is lost
        hand_play.eval_insurance(dealer)
        # this is won (and accounts are settled)
        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        end_cash = hand_play.player.cash
        # insurance won compensates hand lost
        assert end_cash == start_cash + hand_play.betsize  # it's even money

    def test_double_full_win(self):
        class AlwaysDoubleStrategy(GameStrategy):
            def play(self, dealer_hand: Hand, player_hand: Hand, choices: PlayDecision):
                return PlayDecision.DOUBLE

            def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool:
                return NotImplemented

        BET = 5
        player = Player(AlwaysDoubleStrategy(), FixedBettingStrategy(BET))
        start_cash = player.cash  # before bet was charged
        hand_play = HandPlay.from_player(player)  # bet is charged here
        assert hand_play

        dealer = Dealer(hand=Hand(Card("2", "S"), Card("K", "H"), Card("K", "D")))

        hand_play += Card("5", "S")
        hand_play += Card("4", "H")

        hand_play.play(dealer)
        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        end_cash = hand_play.player.cash
        assert end_cash == start_cash + BET * 2  # double bet won

    def test_double_full_loss(self):
        class AlwaysDoubleStrategy(GameStrategy):
            def play(self, dealer_hand: Hand, player_hand: Hand, choices: PlayDecision):
                return PlayDecision.DOUBLE

            def insurance(self, dealer_hand: Hand, player_hand: Hand) -> bool:
                return NotImplemented

        BET = 5
        player = Player(AlwaysDoubleStrategy(), FixedBettingStrategy(BET))
        start_cash = player.cash  # before bet was charged

        hand_play = HandPlay.from_player(player)  # bet is charged here
        assert hand_play

        dealer = Dealer(hand=Hand(Card("K", "H"), Card("K", "D")))

        hand_play += Card("Q", "S")
        hand_play += Card("8", "H")

        hand_play.play(dealer)

        hand_play.eval_hand(dealer)
        end_cash = hand_play.player.cash
        assert end_cash == start_cash - BET * 2  # double bet lost

    def test_cannot_split_if_done(self, hand_play: HandPlay):
        hand_play.done()
        assert not hand_play.can_split()

    def test_cannot_double_if_done(self, hand_play: HandPlay):
        hand_play.done()
        assert not hand_play.can_double()

    def test_cannot_hit_if_done(self, hand_play: HandPlay):
        hand_play.done()
        assert not hand_play.can_hit()

    def test_cannot_surrender_if_done(self, hand_play: HandPlay):
        hand_play.done()
        assert not hand_play.can_surrender()

    def test_cannot_surrender_after_split(self, hand_play: HandPlay):
        dealer = Dealer(hand=Hand(Card("5", "H")))
        hand_play += Card("8", "H")
        hand_play += Card("8", "S")
        split_hands = hand_play.split(dealer)
        assert not split_hands[0].can_surrender()
        assert not split_hands[1].can_surrender()

    def test_cannot_stand_if_done(self, hand_play: HandPlay):
        hand_play.done()
        assert not hand_play.can_stand()

    def test_can_split_two_cards_same_rank(self, hand_play: HandPlay):
        hand_play += Card("8", "S")
        hand_play += Card("8", "H")
        assert hand_play.can_split()

    def test_cannot_split_two_cards_different_ranks(self, hand_play: HandPlay):
        hand_play += Card("8", "S")
        hand_play += Card("9", "H")
        assert not hand_play.can_split()

    def test_cannot_split_three_cards(self, hand_play: HandPlay):
        hand_play += Card("8", "S")
        hand_play += Card("9", "H")
        hand_play += Card("10", "S")
        assert not hand_play.can_split()

    def test_cannot_double_three_cards(self, hand_play: HandPlay):
        hand_play += Card("8", "S")
        hand_play += Card("9", "H")
        hand_play += Card("10", "S")
        assert not hand_play.can_double()

    def test_cannot_surrender_three_cards(self, hand_play: HandPlay):
        hand_play += Card("8", "S")
        hand_play += Card("9", "H")
        hand_play += Card("10", "S")
        assert not hand_play.can_surrender()

    def test_bust_hand_loses(self, hand_play: HandPlay):
        dealer = Dealer()
        while dealer.hand.value < 25:
            dealer.deal_self()

        hand_play += Card("8", "S")
        hand_play += Card("9", "H")
        hand_play += Card("10", "S")

        hand_play.eval_hand(dealer)
        hand_play.cash_out(dealer)
        assert hand_play.result < 0
