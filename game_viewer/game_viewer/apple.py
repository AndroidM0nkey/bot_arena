import pygame

from game_viewer.cell import Cell
import game_viewer.config as c


class Apple(Cell):
    def __init__(self, x, y, r=c.apple_radius, color=c.apple_color):
        Cell.__init__(self, x, y)
        self.radius = r
        self.color = color

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.center, self.radius)