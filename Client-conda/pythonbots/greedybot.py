from bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object
from abc import ABC, abstractmethod
from pythonbots.bot import Bot 
from pythonbots.matrixbfs import MatrixBfs

class GreedyBot(Bot):
    def find_direction(self, field_state: FieldState, m: int, n: int, snake_name: str) -> Direction:
        """Принимает на вход поле, его размеры, имя змеи и выдает направление хода."""

        """Переведем поле в матрицу."""
        matrix = self.field_to_matrix(field_state, n, m)
        
        """Посчитаем расстояния от каждой клетки поля до ближайшего яблока."""
        start_points = []
        for apple in field_state.objects:
            start_points.append((apple[0].y, apple[0].x))
        bfs = MatrixBfs()
        distances = bfs.bfs(matrix, n, m, start_points)


        """Попробуем сделать ходы во все свободные клетки, соседние с головой змеи."""

        snake_state = field_state.snakes[snake_name]
        x, y = snake_state.head.y, snake_state.head.x
        ans = []
        moves = ((0, 1), (0, -1), (1, 0), (-1, 0))
        directions = {(0, 1): Direction.RIGHT(), (0, -1):Direction.LEFT(), (1, 0):Direction.UP, (-1, 0):Direction.DOWN()}

        for move in moves:
            new_cell = (x + move[0], y + move[1])
            new_x, new_y = new_cell[0], new_cell[1]
            """Если клетка внутри таблица и свободна, положим в список расстояние 
                от нее до яблока и нужное направление."""

            if bfs.is_cell_correct(new_cell, n, m) and matrix[new_x][new_y] == 0:
                ans.append(distances[new_x][new_y], directions[move])

        
        """Если змейке некуда ходить, возвращаем произвольный ход и проигрываем:"""
        if len(ans) == 0:
            return Direction.UP()

        """Возвращаем направление хода в сторону клетки, от которой минимальное расстояние до ближайшего яблока."""
        return min(ans, key=lambda i: i[0])[1]