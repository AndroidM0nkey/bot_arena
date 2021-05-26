from bot_arena_server.server import Server
from bot_arena_server.game_loop import run_game_loop
from bot_arena_server.limits import Limits, UpperBound, OptionalUpperBound, Range
from bot_arena_server.work_limit import WorkLimit

import math
from argparse import ArgumentParser, Namespace


__all__ = [
    'main',
]


def uint(s: str) -> int:
    n = int(s)
    if n < 0:
        raise ValueError('Value is negative')
    return n


def ufloat(s: str) -> float:
    f = float(s)
    if f < 0:
        raise ValueError('Value is negative')
    if not math.isfinite(f):
        raise ValueError('Value is NaN or infinite')

    return f


def parse_args() -> Namespace:
    ap = ArgumentParser(prog='bot-arena-server', description='Pythons game server')
    ap.add_argument('--listen-on', default='0.0.0.0', help='IP address or domain name to listen on')
    ap.add_argument('--port', '-p', type=uint, default=23456, help='Port to listen on')
    ap.add_argument('--max-client-name-len', type=uint, default=50, help='Maximum allowed client name length')
    ap.add_argument('--max-field-side', type=uint, default=200, help='Maximum allowed field width/height')
    ap.add_argument('--max-food-items', type=uint, default=50, help='Maximum allowed initial number of food items')
    ap.add_argument('--max-password-len', type=uint, default=500, help='Maximum allowed password length')
    ap.add_argument('--max-room-name-len', type=uint, default=50, help='Maximum allowed room name length')
    ap.add_argument('--max-room-players', type=uint, default=20, help='Maximum allowed number of players in a room')
    ap.add_argument('--max-snake-len', type=uint, default=50, help='Maximum allowed initial snake length')
    ap.add_argument('--max-turn-timeout', type=ufloat, default=None, help='Maximum allowed turn timeout in seconds')
    ap.add_argument('--max-turns', type=uint, default=None, help='Maximum allowed number of turns')
    ap.add_argument('--min-field-side', type=uint, default=5, help='Minimum allowed field width/height')
    ap.add_argument('--turn-delay', type=ufloat, default=0.1, help='Delay between turns in seconds')
    ap.add_argument('--work-units', type=uint, default=500, help='Maximum allowed amount of game preparation work')
    return ap.parse_args()


def make_limits(args: Namespace) -> Limits:
    return Limits(
        field_side_limits = Range(args.min_field_side, args.max_field_side),
        max_client_name_len = UpperBound(args.max_client_name_len),
        max_food_items = UpperBound(args.max_food_items),
        max_password_len = UpperBound(args.max_password_len),
        max_players_in_a_room = args.max_room_players,
        max_room_name_len = UpperBound(args.max_room_name_len),
        max_snake_len = UpperBound(args.max_snake_len),
        max_turn_timeout = OptionalUpperBound(args.max_turn_timeout),
        max_turns = OptionalUpperBound(args.max_turns),
        turn_delay = args.turn_delay,
        work_units = WorkLimit(args.work_units),
    )


def main() -> None:
    args = parse_args()
    limits = make_limits(args)
    server = Server(run_game_loop, limits)
    server.listen(args.listen_on, args.port)


if __name__ == '__main__':
    main()
