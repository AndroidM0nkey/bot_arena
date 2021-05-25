from pythonbots.matrixbfs import MatrixBfs

import pytest

bfs = MatrixBfs()
    
def test_is_cell_correct():
    assert(bfs.is_cell_correct((3, 2), 4, 4) == True)
    assert(bfs.is_cell_correct((0, 0), 4, 3) == True)
    assert(bfs.is_cell_correct((3, 3), 4, 4) == True)
    assert(bfs.is_cell_correct((3, -1), 4, 3) == False)
    assert(bfs.is_cell_correct((3, 4), 3, 4) == False)

def test_make_moves():
    point = (0, 0)
    assert(len(bfs.make_moves(point, 3, 3)) == 2)
    assert((0, 1) in bfs.make_moves(point, 3, 3))
    assert((1, 0) in bfs.make_moves(point, 3, 3))

    point = (1, 1)
    assert(len(bfs.make_moves(point, 3, 3)) == 4)
    assert((0, 1) in bfs.make_moves(point, 3, 3))
    assert((1, 0) in bfs.make_moves(point, 3, 3))
    assert((2, 1) in bfs.make_moves(point, 3, 3))
    assert((1, 2) in bfs.make_moves(point, 3, 3))

def test_bfs():
    matrix = [[0, 0, -1], [0, 0, -1]]
    start_cells = []
    start_cells.append((0, 2))
    distances = bfs.bfs(matrix, 2, 3, start_cells)
    assert(bfs.bfs(matrix, 2, 3, start_cells)[0][0] == 2)
    assert(bfs.bfs(matrix, 2, 3, start_cells)[0][1] == 1)
    assert(bfs.bfs(matrix, 2, 3, start_cells)[1][0] == 3)
    assert(bfs.bfs(matrix, 2, 3, start_cells)[1][1] == 2)