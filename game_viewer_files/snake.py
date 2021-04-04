import pygame

import config as c
from snake_body_peace import SnakeBodyPeace


class Snake:
    def __init__(self, body_pieces):
        self.body_pieces = body_pieces

    def draw(self, surface):
        for i in self.body_pieces:
            i.draw(surface)
