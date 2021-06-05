from bot_arena_client.game_viewer_files import config as c
from bot_arena_client.game_viewer_files.cell import Cell

import pygame


class Apple(Cell):
    def __init__(self, x, y, r=c.apple_radius, color=c.apple_color):
        Cell.__init__(self, x, y, 2 * r, 2 * r)
        self.radius = r
        self.color = color

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.center, self.radius)
