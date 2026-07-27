"""Chess verifier — correctness is PROVEN by perft (the chess-programming standard: exact counts
of legal move sequences), then the rule-verdicts (mate/stalemate/legality/material) build on it."""
from concordance import chess

_KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
_POS3 = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
_FOOLS_MATE = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
_STALEMATE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"


def test_perft_proves_the_move_generator():
    assert chess.perft(chess.parse_fen(chess.START_FEN), 1) == 20
    assert chess.perft(chess.parse_fen(chess.START_FEN), 2) == 400
    assert chess.perft(chess.parse_fen(chess.START_FEN), 3) == 8902
    assert chess.perft(chess.parse_fen(_KIWIPETE), 2) == 2039     # castling + en passant
    assert chess.perft(chess.parse_fen(_POS3), 3) == 2812         # deep, tricky pawns


def test_checkmate_holds_and_is_not_confused_with_stalemate():
    assert chess.is_checkmate(chess.parse_fen(_FOOLS_MATE))
    assert not chess.is_stalemate(chess.parse_fen(_FOOLS_MATE))
    assert chess.verify(_FOOLS_MATE, "checkmate")["verdict"] == "HOLDS"
    assert chess.verify(_FOOLS_MATE, "stalemate")["verdict"] == "BROKEN"


def test_stalemate_holds_and_is_not_check():
    assert chess.is_stalemate(chess.parse_fen(_STALEMATE))
    assert not chess.in_check(chess.parse_fen(_STALEMATE))
    assert chess.verify(_STALEMATE, "stalemate")["verdict"] == "HOLDS"
    assert chess.verify(_STALEMATE, "checkmate")["verdict"] == "BROKEN"


def test_legal_move_verdicts():
    assert chess.verify(chess.START_FEN, "legal_move", "e2e4")["verdict"] == "HOLDS"
    assert chess.verify(chess.START_FEN, "legal_move", "g1f3")["verdict"] == "HOLDS"
    assert chess.verify(chess.START_FEN, "legal_move", "e2e5")["verdict"] == "BROKEN"   # illegal
    assert chess.verify(chess.START_FEN, "legal_move", "e1e2")["verdict"] == "BROKEN"   # king blocked


def test_material_balance():
    assert chess.material(chess.parse_fen(chess.START_FEN).board)["balance"] == 0
    assert chess.verify(chess.START_FEN, "material")["verdict"] == "HOLDS"


def test_bad_fen_declines_never_lies():
    r = chess.verify("not a fen", "check")
    assert r["verdict"] == "INCOMPLETE"      # ERROR is not a false verdict


def test_never_seals_a_false_legal_move():
    # the whole point: an illegal move must come back BROKEN, never HOLDS
    for bad in ("e2e5", "a1a4", "d1d4"):
        assert chess.verify(chess.START_FEN, "legal_move", bad)["verdict"] == "BROKEN"
