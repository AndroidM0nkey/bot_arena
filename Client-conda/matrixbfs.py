from collections import deque

class MatrixBfs:    
    
    @staticmethod
    def is_cell_correct(cell, n, m):
        """Статический метод. Принимает на вход клетку и размеры поля. Вовращает True, если 
        клетка находится внутри поля, и False в ином случае."""
        return cell[0] > -1 and cell[0] < n and cell[1] > -1 and cell[1] < m


    def make_moves(self, cell, n, m):
        """Принимает на вход клетку поля и возвращает список 
        соседних по стороне клеток."""

        moves = ((0, 1), (0, -1), (1, 0), (-1, 0))
        new_cells = []

        for move in moves:
            new_cell = (cell[0] + move[0], cell[1] + move[1])
            if self.is_cell_correct(new_cell, n, m):
                new_cells.append(new_cell)
        return new_cells

    def bfs(self, matrix, n, m, start_cells):
        """Реализует алгоритм обхода в ширину, начиная с множества клеток start_cells. Принимает 
        на вход матрицу, где 0 - свободные клетки, -1 - занятые, размеры матрицы и множество 
        стартовых клеток. Возвращает матрицу distances, в которой в каждой клетке записано расстояние 
        до ближайшей из стартовых."""

        """Очередь, необходимая для BFS. Константа, равная бесконечности, которой 
        будут обозначаться клетки, в которым алгоритм еще не побывал. Матрица 
        расстояний."""
        bfs_queue = deque()
        infinity = 1000
        distances = [[infinity for i in range(m)] for j in range(n)]
        
        """Добавление стартовых вершин в очередь."""
        for start_cell in start_cells:
            bfs_queue.append(start_cell)
            
            x, y = start_cell[0], start_cell[1]
            distances[x][y] = 0

        """Алгоритм продолжает работу, пока не кончились непосещенные вершины."""
        while len(bfs_queue) != 0:
            cell = bfs_queue.popleft()
            x, y = cell[0], cell[1]
            for new_cell in self.make_moves(cell, n, m):
                
                """Проверяем, что соседняя клетка находится внутри поля свободна, и мы в ней еще не были,
                и добавляем в очередь, подсчитывая расстояние."""
                
                new_x, new_y = new_cell[0], new_cell[1]
                if matrix[new_x][new_y] == 0 and distances[new_x][new_y] == infinity:
                        distances[new_x][new_y] = distances[x][y] + 1
                        bfs_queue.append((new_x, new_y))

        return distances