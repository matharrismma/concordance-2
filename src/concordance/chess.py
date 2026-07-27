"""Chess — a deterministic move/position verifier (game theory, applied and checkable).

Matt, 2026-07-26: "Chess as well. We understand game theory. We can apply that to chess and build
it in." The engine does not PLAY (no evaluation, no search for a best move); it VERIFIES what is
true of a position by the rules of chess — is this move legal, is the side to move in check, is it
checkmate or stalemate, what is the material. Every answer is deterministic and re-checkable, so a
chess claim seals like any other verdict.

Correctness is proven, not asserted: the move generator is validated by PERFT — the exact number
of legal move sequences from known positions (the chess-programming standard). If perft matches on
the start position AND the castling/en-passant/promotion test positions, the rules are right.

Stdlib only. Board is a list of 64 squares, index 0 = a1 … 63 = h8; white pieces PNBRQK, black
pnbrqk, '.' empty.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

WHITE_PIECES = set("PNBRQK")
BLACK_PIECES = set("pnbrqk")

_FILES = "abcdefgh"


def sq(r: int, c: int) -> int:
    return r * 8 + c


def rc(s: int) -> Tuple[int, int]:
    return divmod(s, 8)


def sq_name(s: int) -> str:
    r, c = rc(s)
    return f"{_FILES[c]}{r + 1}"


def name_sq(name: str) -> int:
    return sq(int(name[1]) - 1, _FILES.index(name[0]))


class Position:
    __slots__ = ("board", "white", "castle", "ep", "half", "full")

    def __init__(self, board, white, castle, ep, half, full):
        self.board = board          # list[64]
        self.white = white          # bool: white to move
        self.castle = castle        # set of 'K','Q','k','q'
        self.ep = ep                # en-passant target square index, or None
        self.half = half
        self.full = full

    def copy(self) -> "Position":
        return Position(self.board[:], self.white, set(self.castle), self.ep, self.half, self.full)


def parse_fen(fen: str) -> Position:
    parts = fen.strip().split()
    if len(parts) < 4:
        raise ValueError("FEN needs at least 4 fields")
    rows = parts[0].split("/")
    if len(rows) != 8:
        raise ValueError("FEN board must have 8 ranks")
    board = ["."] * 64
    for i, row in enumerate(rows):
        r = 7 - i                    # FEN lists rank 8 first
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
            else:
                if ch not in WHITE_PIECES and ch not in BLACK_PIECES:
                    raise ValueError(f"bad piece {ch!r}")
                board[sq(r, c)] = ch
                c += 1
        if c != 8:
            raise ValueError("rank does not sum to 8 files")
    white = parts[1] == "w"
    castle = set(ch for ch in parts[2] if ch in "KQkq")
    ep = None if parts[2] == "-" or parts[3] == "-" else name_sq(parts[3])
    half = int(parts[4]) if len(parts) > 4 else 0
    full = int(parts[5]) if len(parts) > 5 else 1
    return Position(board, white, castle, ep, half, full)


def _is_white(p: str) -> bool:
    return p in WHITE_PIECES


_KNIGHT = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
_KING = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
_BISHOP = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
_ROOK = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def attacked(board: List[str], s: int, by_white: bool) -> bool:
    """Is square `s` attacked by a piece of the given color?"""
    r, c = rc(s)
    # pawns: a white pawn attacks the squares diagonally in FRONT of it (from r-1); so square s is
    # attacked by a white pawn sitting at (r-1, c±1).
    pr = r - 1 if by_white else r + 1
    if 0 <= pr < 8:
        for dc in (-1, 1):
            cc = c + dc
            if 0 <= cc < 8:
                p = board[sq(pr, cc)]
                if p == ("P" if by_white else "p"):
                    return True
    # knights
    for dr, dc in _KNIGHT:
        rr, cc = r + dr, c + dc
        if 0 <= rr < 8 and 0 <= cc < 8:
            p = board[sq(rr, cc)]
            if p == ("N" if by_white else "n"):
                return True
    # king
    for dr, dc in _KING:
        rr, cc = r + dr, c + dc
        if 0 <= rr < 8 and 0 <= cc < 8:
            p = board[sq(rr, cc)]
            if p == ("K" if by_white else "k"):
                return True
    # sliding: bishop/queen (diagonals), rook/queen (orthogonals)
    for dirs, pieces in ((_BISHOP, ("B", "Q") if by_white else ("b", "q")),
                         (_ROOK, ("R", "Q") if by_white else ("r", "q"))):
        for dr, dc in dirs:
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                p = board[sq(rr, cc)]
                if p != ".":
                    if p in pieces:
                        return True
                    break
                rr += dr
                cc += dc
    return False


def king_square(board: List[str], white: bool) -> Optional[int]:
    k = "K" if white else "k"
    for s in range(64):
        if board[s] == k:
            return s
    return None


def in_check(pos: Position) -> bool:
    ks = king_square(pos.board, pos.white)
    if ks is None:
        return False
    return attacked(pos.board, ks, by_white=not pos.white)


# a move: (from, to, promo|None, flag) where flag in {"", "ep", "castleK", "castleQ", "2"}
Move = Tuple[int, int, Optional[str], str]


def _pseudo_moves(pos: Position) -> List[Move]:
    board, white = pos.board, pos.white
    own = WHITE_PIECES if white else BLACK_PIECES
    moves: List[Move] = []
    for s in range(64):
        p = board[s]
        if p == "." or p not in own:
            continue
        r, c = rc(s)
        up = p.upper()
        if up == "P":
            d = 1 if white else -1
            start_rank = 1 if white else 6
            promo_rank = 7 if white else 0
            # forward one
            r1 = r + d
            if 0 <= r1 < 8 and board[sq(r1, c)] == ".":
                if r1 == promo_rank:
                    for pr in ("Q", "R", "B", "N"):
                        moves.append((s, sq(r1, c), pr, ""))
                else:
                    moves.append((s, sq(r1, c), None, ""))
                    # forward two
                    if r == start_rank and board[sq(r + 2 * d, c)] == ".":
                        moves.append((s, sq(r + 2 * d, c), None, "2"))
            # captures + en passant
            for dc in (-1, 1):
                cc = c + dc
                if not (0 <= cc < 8):
                    continue
                t = sq(r1, cc) if 0 <= r1 < 8 else None
                if t is None:
                    continue
                tp = board[t]
                if tp != "." and (tp in BLACK_PIECES if white else tp in WHITE_PIECES):
                    if r1 == promo_rank:
                        for pr in ("Q", "R", "B", "N"):
                            moves.append((s, t, pr, ""))
                    else:
                        moves.append((s, t, None, ""))
                elif pos.ep is not None and t == pos.ep:
                    moves.append((s, t, None, "ep"))
        elif up == "N":
            for dr, dc in _KNIGHT:
                rr, cc = r + dr, c + dc
                if 0 <= rr < 8 and 0 <= cc < 8:
                    tp = board[sq(rr, cc)]
                    if tp == "." or (tp in BLACK_PIECES if white else tp in WHITE_PIECES):
                        moves.append((s, sq(rr, cc), None, ""))
        elif up == "K":
            for dr, dc in _KING:
                rr, cc = r + dr, c + dc
                if 0 <= rr < 8 and 0 <= cc < 8:
                    tp = board[sq(rr, cc)]
                    if tp == "." or (tp in BLACK_PIECES if white else tp in WHITE_PIECES):
                        moves.append((s, sq(rr, cc), None, ""))
            # castling — rights present, squares empty, king not in/through/into check
            moves.extend(_castle_moves(pos, s))
        else:
            dirs = _BISHOP if up == "B" else _ROOK if up == "R" else _KING  # queen uses both
            if up == "Q":
                dirs = _BISHOP + _ROOK
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                while 0 <= rr < 8 and 0 <= cc < 8:
                    tp = board[sq(rr, cc)]
                    if tp == ".":
                        moves.append((s, sq(rr, cc), None, ""))
                    else:
                        if tp in BLACK_PIECES if white else tp in WHITE_PIECES:
                            moves.append((s, sq(rr, cc), None, ""))
                        break
                    rr += dr
                    cc += dc
    return moves


def _castle_moves(pos: Position, ks: int) -> List[Move]:
    board, white = pos.board, pos.white
    out: List[Move] = []
    r = 0 if white else 7
    if ks != sq(r, 4):
        return out
    opp = not white
    if attacked(board, ks, by_white=opp):
        return out  # cannot castle out of check
    # kingside
    right_k = "K" if white else "k"
    if right_k in pos.castle and board[sq(r, 5)] == "." and board[sq(r, 6)] == "." \
            and board[sq(r, 7)] == ("R" if white else "r"):
        if not attacked(board, sq(r, 5), opp) and not attacked(board, sq(r, 6), opp):
            out.append((ks, sq(r, 6), None, "castleK"))
    right_q = "Q" if white else "q"
    if right_q in pos.castle and board[sq(r, 3)] == "." and board[sq(r, 2)] == "." \
            and board[sq(r, 1)] == "." and board[sq(r, 0)] == ("R" if white else "r"):
        if not attacked(board, sq(r, 3), opp) and not attacked(board, sq(r, 2), opp):
            out.append((ks, sq(r, 2), None, "castleQ"))
    return out


def apply_move(pos: Position, m: Move) -> Position:
    fr, to, promo, flag = m
    n = pos.copy()
    b = n.board
    p = b[fr]
    white = pos.white
    b[fr] = "."
    # en passant capture removes the pawn behind the target
    if flag == "ep":
        cap = to - 8 if white else to + 8
        b[cap] = "."
    # place piece (with promotion)
    if promo:
        b[to] = promo if white else promo.lower()
    else:
        b[to] = p
    # rook hop on castling
    if flag == "castleK":
        r = 0 if white else 7
        b[sq(r, 5)] = b[sq(r, 7)]
        b[sq(r, 7)] = "."
    elif flag == "castleQ":
        r = 0 if white else 7
        b[sq(r, 3)] = b[sq(r, 0)]
        b[sq(r, 0)] = "."
    # castling rights: king or rook moving/being captured revokes
    up = p.upper()
    if up == "K":
        n.castle.discard("K" if white else "k")
        n.castle.discard("Q" if white else "q")
    for corner, right in ((sq(0, 0), "Q"), (sq(0, 7), "K"), (sq(7, 0), "q"), (sq(7, 7), "k")):
        if fr == corner or to == corner:
            n.castle.discard(right)
    # en-passant target for a double push
    n.ep = ((fr + to) // 2) if flag == "2" else None
    n.half = 0 if (up == "P" or pos.board[to] != ".") else pos.half + 1
    n.full = pos.full + (0 if white else 1)
    n.white = not white
    return n


def legal_moves(pos: Position) -> List[Move]:
    """Every fully-legal move: a pseudo-move that does not leave the mover's own king in check."""
    out = []
    for m in _pseudo_moves(pos):
        n = apply_move(pos, m)
        ks = king_square(n.board, pos.white)     # the side that just moved
        if ks is not None and not attacked(n.board, ks, by_white=not pos.white):
            out.append(m)
    return out


def perft(pos: Position, depth: int) -> int:
    if depth == 0:
        return 1
    total = 0
    for m in legal_moves(pos):
        total += perft(apply_move(pos, m), depth - 1)
    return total


def is_checkmate(pos: Position) -> bool:
    return in_check(pos) and not legal_moves(pos)


def is_stalemate(pos: Position) -> bool:
    return (not in_check(pos)) and not legal_moves(pos)


_VALUE = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}


def material(board: List[str]) -> Dict[str, int]:
    w = sum(_VALUE[p.upper()] for p in board if p in WHITE_PIECES)
    b = sum(_VALUE[p.upper()] for p in board if p in BLACK_PIECES)
    return {"white": w, "black": b, "balance": w - b}


def _move_str(m: Move) -> str:
    fr, to, promo, _flag = m
    return sq_name(fr) + sq_name(to) + (promo.lower() if promo else "")


def verify(fen: str, claim: str, move: Optional[str] = None) -> Dict:
    """Verify a claim about a position by the rules. claim ∈ {legal_move, check, checkmate,
    stalemate, material}. Returns a derivation-style result (verdict + trail) — deterministic,
    so the caller can seal it. Never plays; only states what is true."""
    try:
        pos = parse_fen(fen)
    except Exception as e:  # noqa: BLE001
        return {"verdict": "INCOMPLETE", "detail": f"unreadable FEN: {e}", "steps": 1,
                "confirmed_steps": 0, "trail": [{"domain": "chess", "status": "ERROR", "detail": str(e)}]}
    side = "White" if pos.white else "Black"
    if claim == "legal_move":
        if not move:
            return {"verdict": "INCOMPLETE", "detail": "no move given", "steps": 1,
                    "confirmed_steps": 0, "trail": [{"domain": "chess", "status": "ERROR"}]}
        legals = {_move_str(m) for m in legal_moves(pos)}
        ok = move.strip().lower() in legals
        return {"verdict": "HOLDS" if ok else "BROKEN",
                "detail": f"{move} is {'a legal' if ok else 'NOT a legal'} move for {side}.",
                "steps": 1, "confirmed_steps": 1 if ok else 0,
                "trail": [{"domain": "chess", "claim": f"{move} legal for {side} in {fen}",
                           "status": "PASS" if ok else "MISMATCH",
                           "detail": f"{len(legals)} legal moves exist; {move} " +
                                     ("is among them" if ok else "is not")}]}
    prop = {"check": in_check(pos), "checkmate": is_checkmate(pos), "stalemate": is_stalemate(pos)}
    if claim in prop:
        ok = prop[claim]
        return {"verdict": "HOLDS" if ok else "BROKEN",
                "detail": f"{side} to move: {claim} is {ok}.", "steps": 1,
                "confirmed_steps": 1 if ok else 0,
                "trail": [{"domain": "chess", "claim": f"{claim} for {side} in {fen}",
                           "status": "PASS" if ok else "MISMATCH", "detail": f"{claim}={ok}"}]}
    if claim == "material":
        mat = material(pos.board)
        return {"verdict": "HOLDS", "detail": f"material — white {mat['white']}, black {mat['black']} "
                f"(balance {mat['balance']:+d}).", "steps": 1, "confirmed_steps": 1,
                "trail": [{"domain": "chess", "claim": "material count", "status": "PASS",
                           "detail": str(mat)}]}
    return {"verdict": "INCOMPLETE", "detail": f"unknown claim {claim!r}", "steps": 1,
            "confirmed_steps": 0, "trail": [{"domain": "chess", "status": "ERROR"}]}


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
