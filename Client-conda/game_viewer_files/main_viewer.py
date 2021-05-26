from bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object

from game_viewer_files.apple import Apple
from game_viewer_files.snake_body_peace import SnakeBodyPeace
from game_viewer_files.snake import Snake
import game_viewer_files.config as c
import pygame
import random


class Viewer:
    def __init__(self):
        self.all_snakes = {}
        self.player_colors = [(0, 255, 0), (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 0),
                         (200, 0, 255)]

    def reset(self):
        self.all_snakes = {}
        self.player_colors = [(0, 255, 0), (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 0),
                              (200, 0, 255)]

    def invert(self, p: int, field_height: int):
        return field_height - 1 - p

    def get_message_and_display(self, cur_state: FieldState, field_height: int, field_width: int,
                                score):
        cell_width = int(c.screen_width / max(field_height, field_width))
        surface = pygame.display.set_mode((field_width * cell_width, field_height * cell_width))
        colors_cnt = -1
        snakes = []
        surface.fill(pygame.Color('black'))
        # drawing players
        if len(self.all_snakes) == 0:
            self.all_snakes = cur_state.snakes
        for snake_name in self.all_snakes.keys():
            if snake_name in cur_state.snakes.keys():
                snake_state = cur_state.snakes[snake_name]
                self.all_snakes[snake_name] = snake_state
                snake_alive = True
            else:
                snake_state = self.all_snakes[snake_name]
                snake_alive = False
            colors_cnt += 1
            if colors_cnt >= len(self.player_colors):
                self.player_colors.append((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
            snake_peaces = []
            cur_x = snake_state.head.x * cell_width
            cur_y = self.invert(snake_state.head.y, field_height) * cell_width
            snake_peaces.append(SnakeBodyPeace(cur_x, cur_y, cell_width, self.player_colors[colors_cnt]))
            for peace in snake_state.tail:
                if peace == Direction.UP():
                    cur_y -= cell_width
                if peace == Direction.DOWN():
                    cur_y += cell_width
                if peace == Direction.LEFT():
                    cur_x -= cell_width
                if peace == Direction.RIGHT():
                    cur_x += cell_width
                snake_peaces.append(SnakeBodyPeace(cur_x, cur_y, cell_width, self.player_colors[colors_cnt]))
            cur_snake = Snake(snake_peaces, snake_alive, snake_name)
            snakes.append(cur_snake)
        snakes = sorted(snakes, key=lambda elem: elem.get_alive_status())
        for snake in snakes:
            snake.draw(surface)
        # drawing objects
        for i in range(len(cur_state.objects)):
            apple = Apple(cur_state.objects[i][0].x * cell_width, self.invert(cur_state.objects[i][0].y, field_height) *
                          cell_width, cell_width // 2)
            apple.draw(surface)
        # drawing score distribution
        font_size = 30
        whitespace_size = 15
        myfont = pygame.font.SysFont('Arial', font_size)
        textsurface = myfont.render('Score:', True, (255, 255, 255))
        surface.blit(textsurface, (0, 0))
        cur_x_coord = textsurface.get_rect().width + whitespace_size
        for snake in snakes:
            snake_name = snake.get_name()
            if score is None:
                snake_score = 0
            else:
                snake_score = score[snake_name]
            textsurface = myfont.render(str(snake_score), True, snake.get_color())
            surface.blit(textsurface, (cur_x_coord, 0))
            cur_x_coord += textsurface.get_rect().width + whitespace_size
        pygame.display.update()
        return