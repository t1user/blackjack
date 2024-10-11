import pytest

from blackjack.engine import DECK, Card, Hand, NotEnoughCash, Player, Shoe
from blackjack.strategies import FixedBettingStrategy, RandomStrategy


def test_Card_cannot_be_instantiated_with_wrong_suit():
    with pytest.raises(ValueError):
        Card("K", "A")


def test_Card_cannot_be_instantiated_with_wrong_rank():
    with pytest.raises(ValueError):
        Card("11", "D")


def test_ace_value():
    ace_card = Card("A", "H")
    assert ace_card.value == 11


def test_ace_soft_value():
    ace_card = Card("A", "D")
    assert ace_card.soft_value == 1


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


def test_shoe_has_correct_number_of_cards():
    shoe = Shoe(6)
    assert len(shoe) == 6 * 52


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


def test_hand_with_ace_hard_value():
    # It's (10, 20) so if no more cards taken the value that matters is 20
    assert Hand(Card("A", "D"), Card("9", "H")).value == 20


def test_hand_with_ace_soft_value():
    assert Hand(Card("A", "D"), Card("9", "H"), Card("8", "C")).value == 18


def test_not_bust_with_ace():
    # hard value is bust but soft not
    assert not Hand(Card("A", "D"), Card("9", "H"), Card("8", "C")).is_bust()


def test_bust_with_ace():
    # both soft and hard values are bust
    assert Hand(
        Card("A", "D"), Card("9", "H"), Card("8", "C"), Card("10", "D")
    ).is_bust()


def test_Hand_eq():
    hand1 = Hand(Card("A", "D"), Card("9", "H"), Card("8", "C"))
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
