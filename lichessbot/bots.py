import threading
import berserk
import stockfish
import logging
import chess
import random

from .game import Game

logger = logging.getLogger(__name__)


class ChessBot:
    def __init__(self, api_key: str):
        session = berserk.TokenSession(api_key)
        self.client = berserk.Client(session)
        self.user_id = self.client.account.get()['id']

    def select_move(self, board: chess.Board) -> str:
        """chess.Board object -> UCI move string"""
        raise NotImplementedError

    def _handle_event(self, event):
        if event['type'] == 'challenge':
            logger.info("Accepting challenge!")
            challenge_id = event['challenge']['id']
            self.client.bots.accept_challenge(challenge_id)
        elif event['type'] == 'gameStart':
            game_id = event['game']['id']
            game = Game(client=self.client,
                        user_id=self.user_id,
                        game_id=game_id,
                        select_move_cb=self.select_move)
            threading.Thread(target=game.run).start()

    def run(self):
        logger.info(f'{self.__class__.__name__} started.')
        events = self.client.bots.stream_incoming_events()
        for event in events:
            logger.info(event)
            self._handle_event(event)


class MinimaxBot(ChessBot):
    def __init__(self, depth: int = 4, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.depth = depth

    @staticmethod
    def evaluate(board: chess.Board):
        """Simple valuation function.

        Just sums the piece values.
        """
        pieces = board.epd().split()[0]
        piece_values = {
            'p': 1,
            'n': 3,
            'b': 3.25,
            'k': 10000,
            'q': 9,
            'r': 5,
            'P': -1,
            'N': -3,
            'B': -3.25,
            'K': -10000,
            'Q': -9,
            'R': -5
        }
        return sum(piece_values.get(c, 0) for c in pieces)

    def _minimax(self, board: chess.Board, depth: int,
                 alpha: float = float('-inf'),
                 beta: float = float('inf')):
        if depth == 0 and any(board.legal_moves):
            return self.evaluate(board), None
        # Draw
        elif (board.can_claim_draw() or
              board.is_stalemate() or
              board.is_insufficient_material()):
            return 0, None
        # White wins
        elif board.is_checkmate() and board.turn == chess.BLACK:
            return float('inf'), None
        # Black wins
        elif board.is_checkmate() and board.turn == chess.WHITE:
            return float('-inf'), None

        best_eval, best_move = float('-inf'), None
        for move in random.sample(list(board.legal_moves), board.legal_moves.count()):
            board.push_uci(move.uci())
            cur_eval, cur_move = self._minimax(board, depth - 1, -beta, -alpha)
            cur_eval = -cur_eval
            board.pop()
            if best_eval < cur_eval:
                best_eval = cur_eval
                alpha = cur_eval
                best_move = move
            if best_eval >= beta:
                break
        return best_eval, best_move

    def select_move(self, board: chess.Board) -> str:
        value, best_move = self._minimax(board, self.depth)
        logger.info(f"Evaluation: {value:.2f}")
        return best_move.uci()


class StockfishBot(ChessBot):
    def __init__(self, sf_path: str, level: int = 20, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = stockfish.Stockfish(sf_path)
        self.engine.set_skill_level(level)

    def select_move(self, board: chess.Board) -> str:
        self.engine.set_position(board.move_stack)
        return self.engine.get_best_move()


class RandomBot(ChessBot):
    def select_move(self, board: chess.Board) -> str:
        return random.choice(list(board.legal_moves)).uci()
