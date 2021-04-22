import pygame

from game_viewer_files.cell import Cell


class SnakeBodyPeace(Cell):
    def __init__(self, x, y, cell_width, color):
        Cell.__init__(self, x, y, cell_width, cell_width)
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.left + 1, self.top + 1, self.width - 1, self.width - 1))
