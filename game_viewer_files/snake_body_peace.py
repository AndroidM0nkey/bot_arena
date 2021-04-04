import pygame

from cell import Cell
import config as c


class SnakeBodyPeace(Cell):
    def __init__(self, x, y, color):
        Cell.__init__(self, x, y)
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.left + 1, self.top + 1, self.width - 1, self.width - 1))
