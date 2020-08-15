import berserk
import chess
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class Game:
    def __init__(self,
                 client: berserk.Client,
                 user_id: str,
                 game_id: str,
                 select_move_cb: Callable[[chess.Board], str]):
        self.client = client
        self.user_id = user_id
        self.game_id = game_id
        self.select_move = select_move_cb
        self.board = chess.Board()

        self.stream = client.bots.stream_game_state(game_id)

        event = next(self.stream)
        if user_id == event['white']['id']:
            self.color = chess.WHITE
        elif user_id == event['black']['id']:
            self.color = chess.BLACK
        else:
            raise RuntimeError("This bot is not playing in the game.")

    def uci_to_san(self, move: str):
        move = chess.Move.from_uci(move)
        return self.board.san(move)

    def move(self):
        move = self.select_move(self.board)
        self.board.push_uci(move)
        self.client.bots.make_move(self.game_id, move)

        # Skip the confirmation event
        next(self.stream)
        logger.info(move)

    def _run(self):
        if self.color == chess.WHITE:
            # We go first; make a move
            self.move()
        for event in self.stream:
            if event.get('status') == 'started':
                last_move = event['moves'].split()[-1]
                self.board.push_uci(last_move)
                self.move()
            elif 'winner' in event:
                # Game is over
                break
            logger.info(event)

    def run(self):
        try:
            self._run()
        except IOError as e:
            logger.error(e)
        except Exception:
            self.client.bots.resign_game(self.game_id)
            raise
