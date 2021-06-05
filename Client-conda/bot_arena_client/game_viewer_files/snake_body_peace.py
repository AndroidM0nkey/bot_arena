from bot_arena_client.game_viewer_files.cell import Cell

import pygame


class SnakeBodyPeace(Cell):
    def __init__(self, x, y, cell_width, color):
        Cell.__init__(self, x, y, cell_width, cell_width)
        self.color = color

    def get_color(self):
        return self.color

    def draw(self, surface, is_alive):
        pygame.draw.rect(surface, self.color, (self.left + 1, self.top + 1, self.width - 2, self.width - 2))
        if is_alive is False:
            pygame.draw.rect(surface, (0, 0, 0), (self.left + 2, self.top + 2, self.width - 4, self.width - 4))
