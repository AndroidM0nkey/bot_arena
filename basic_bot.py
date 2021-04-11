from bot_arena_proto.bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object
from collections import deque



class Bot:

    """Это самая базовая версия игрового бота, он взаимодействует практически
    напрямую с сервером. Бот получает на вход(функция find_direction) состояние поля и имя змейки,
    чья сейчас очередь ходить, и выдает в ответ direction - направление хода. Бот основан на алгоритме
    поиска в ширину и делает ход в направление клетки, от которой до яблока наименьшее расстояние."""

    moves = ((0, 1), (0, -1), (1, 0), (-1, 0))
    inf = 1000

    """Все возможные ходы в терминах таблицы, константа = бесконечности."""

    
    def field_to_matrix(self, field_state : FieldState, n: int, m : int):
        """Преобразовывает объект класса FieldState в матрицу, в которой все элементы = 0,
        если это пустая клетка, а иначе(яблоко, змейка) = -1. Так же возвращает 
        матрицу такого же размера, как и поле, составленную из +inf - в нее 
        мы будем записывать расстояния.""" 

        matrix = [[0 for i in range(n)] for j in range(m)]
        distances = [[Bot.inf for i in range(n)] for j in range(m)]
        
        apple = field_state.objects[0][0]
        """Координаты яблока."""

        matrix[apple.x][apple.y] = -1

        for snake_state in field_state.snakes.values():
            x = snake_state.head.x
            y = snake_state.head.y
            matrix[x][y] = -1

            """Идем по всем клеткам змейки, начиная с головы, и записываем в matrix -1."""

            for snake_cell in snake_state.tail:
                if snake_cell == Direction.UP():
                    x -= 1
                if snake_cell == Direction.DOWN():
                    x += 1
                if snake_cell == Direction.LEFT():
                    y -= 1
                if snake_cell == Direction.RIGHT():
                    y += 1
                matrix[x][y] = -1
            
        return (matrix, distances)

    def is_cell_correct(self, point, n, m):
        """Проверка на то, что координаты клетки помещаются в наше поле."""

        return point[0] > -1 and point [0] < n and point[1] > -1 and point[1] < m

    def bfs(self, matrix, distances, n, m, start_point):
        """Реализует алгоритм обхода в ширину, начиная со start_point."""

        """Добавляем стартовую вершину в очередь."""
        bfs_queue = deque()
        bfs_queue.append((start_point.x, start_point.y))
        distances[start_point.x][start_point.y] = 0

        """Алгоритм продолжает работу, пока не кончились непосещенные вершины."""

        while len(bfs_queue) != 0:
            cell = bfs_queue.popleft()
            x = cell[0]
            y = cell[1]
            for move in Bot.moves:
                """Считаем координаты соседней вершины."""
                next_cell = (x + move[0], y + move[1])
                next_x = next_cell[0]
                next_y = next_cell[1]
                
                """Проверяем, что такая клетка есть, свободна, и мы в ней еще не были,
                и добавляем в очередь, подсчитывая расстояние."""
                if self.is_cell_correct(next_cell, n, m):
                    if matrix[next_x][next_y] == 0:
                        if distances[next_x][next_y] == Bot.inf: 
                            distances[next_x][next_y] = distances[x][y] + 1
                            bfs_queue.append((next_x, next_y))

        return distances



    def find_direction(self, field_state : FieldState, n : int, m : int, snake_name : str):
        """Принимает на вход поле, имя змеи и выдает направление хода."""

        """Посчитаем расстояния от яблока до каждой свободной клетки поля."""
        matrix, distances = self.field_to_matrix(field_state, n, m)
        apple = field_state.objects[0][0]
        distances = self.bfs(matrix, distances, n, m, apple)
    
        snake_state = field_state.snakes[snake_name]
        x = snake_state.head.x
        y = snake_state.head.y

        ans = []
        
        """Попробуем сделать ходы во все свободные клетки, соседние с головой змеи."""
        
        for move in Bot.moves:
            next_cell = (x + move[0], y + move[1])
            next_x = next_cell[0]
            next_y = next_cell[1]
            if self.is_cell_correct(next_cell, n, m):
                if matrix[next_x][next_y] == 0:

                    """Если клетка внутри таблица и свободна, 
                        положим в список расстояние от нее до яблока и нужное 
                            направление."""
                    
                    if (move == (0, 1)):
                        ans.append((distances[next_x][next_y], Direction.RIGHT()))
                    if (move == (0, -1)):
                        ans.append((distances[next_x][next_y], Direction.LEFT()))
                    if (move == (1, 0)):
                        ans.append((distances[next_x][next_y], Direction.UP()))
                    if (move == (-1, 0)):
                        ans.append((distances[next_x][next_y], Direction.DOWN()))
        
        """Если змейке некуда ходить:"""
        if len(ans) == 0:
            return "Impossible"

        """Возвращаем направление хода в сторону клетки, от которой минимальное расстояние до клетки с яблоком."""

        return min(ans, key = lambda i : i[0])[1]




