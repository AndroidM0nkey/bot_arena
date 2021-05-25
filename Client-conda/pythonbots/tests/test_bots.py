from bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object
from pythonbots.bot import Bot
from pythonbots.greedybot import GreedyBot
from pythonbots.agressivebot import AgressiveBot
from pythonbots.runbot import RunBot
from abc import ABC, abstractmethod


import pytest

greedy_bot = GreedyBot()
agressive_bot = AgressiveBot()
run_bot = RunBot()
    
def test_field_to_matrix():
    snake1 = SnakeState(head=Point(2, 1), tail=[Direction.RIGHT(), Direction.DOWN()])
    snake2 = SnakeState(head=Point(2, 3), tail=[])
    apple1 = (Point(1, 1), Object.FOOD())
    apple2 = (Point(0, 3), Object.FOOD())
    apple3 = (Point(3, 3), Object.FOOD())
    field_state = FieldState(snakes={'1': snake1, '2': snake2}, objects=[apple1, apple2, apple3])
    matrix = [[0, 0, 0, -1], [0, 0, -1, -1], [0, 0, 0, 0], [0, 0, -1, 0], [0, 0, 0, 0]]    
    assert(matrix == greedy_bot.field_to_matrix(field_state, 5, 4))


    snake1 = SnakeState(head=Point(2, 1), tail=[Direction.RIGHT(), Direction.DOWN(), Direction.LEFT(), Direction.LEFT(), Direction.LEFT(), Direction.UP()])
    field_state = FieldState(snakes={'1': snake1}, objects=[apple1, apple2, apple3])
    matrix = [[-1, -1, -1, -1], [-1, 0, -1, -1], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]        
    assert(matrix == greedy_bot.field_to_matrix(field_state, 5, 4))

def test_find_direction():
    snake1 = SnakeState(head=Point(2, 1), tail=[Direction.RIGHT(), Direction.DOWN()])
    snake2 = SnakeState(head=Point(2, 3), tail=[])
    apple1 = (Point(1, 1), Object.FOOD())
    apple2 = (Point(0, 3), Object.FOOD())
    apple3 = (Point(3, 3), Object.FOOD())
    field_state = FieldState(snakes={'1': snake1, '2': snake2}, objects=[apple1, apple2, apple3])
    
    assert(Direction.LEFT() == greedy_bot.find_direction(field_state, 4, 5, '1'))
    assert(Direction.UP() == agressive_bot.find_direction(field_state, 4, 5, '1'))
    assert(Direction.UP() == run_bot.find_direction(field_state, 4, 5, '1'))


    
    