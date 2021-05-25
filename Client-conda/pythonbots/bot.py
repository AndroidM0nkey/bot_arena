from typing import List
from bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object
from abc import ABC, abstractmethod
from typing import List

class Bot(ABC):
    """Это самая базовая версия игрового бота, он взаимодействует практически
    напрямую с сервером. Бот получает на вход(функция find_direction) состояние поля и имя змейки,
    чья сейчас очередь ходить, и выдает в ответ direction - направление хода. Бот основан на алгоритме
    поиска в ширину и делает ход в направление клетки, от которой до яблока наименьшее расстояние."""


    @staticmethod
    def field_to_matrix(field_state: FieldState, n: int, m: int) -> List[List[int]]:
        """Преобразовывает объект класса FieldState в матрицу, в которой все элементы = 0,
        если это пустая клетка, а иначе(яблоко, змейка) = -1."""

        matrix = [[0 for i in range(m)] for j in range(n)]
       

        for snake_state in field_state.snakes.values():
            
            x = snake_state.head.x
            y = snake_state.head.y
            matrix[y][x] = -1

            """Идем по всем клеткам змейки, начиная с головы, и записываем в matrix -1."""

            for snake_cell in snake_state.tail:
                if snake_cell == Direction.UP():
                    y += 1
                if snake_cell == Direction.DOWN():
                    y -= 1
                if snake_cell == Direction.LEFT():
                    x -= 1
                if snake_cell == Direction.RIGHT():
                    x += 1
                matrix[y][x] = -1

        return matrix

    

    @abstractmethod
    def find_direction(self, field_state: FieldState, n: int, m: int, snake_name: str):
        pass 

