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
        self.colors_mapping = {}
        self.height = self.width = 0

    def reset(self):
        self.all_snakes = {}
        self.player_colors = [(0, 255, 0), (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 0),
                              (200, 0, 255)]
        self.colors_mapping = {}
        self.height = self.width = 0

    def invert(self, p: int, field_height: int):
        return field_height - 1 - p

    def get_message_and_display(self, cur_state: FieldState, field_height: int, field_width: int,
                                score):
        cell_width = int(c.screen_width / max(field_height, field_width))
        self.height = field_height
        self.width = field_width
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
            self.colors_mapping[snake_name] = self.player_colors[colors_cnt]
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
        my_font = pygame.font.SysFont('Arial', font_size)
        text_surface = my_font.render('Score:', True, (255, 255, 255))
        surface.blit(text_surface, (0, 0))
        cur_x_coord = text_surface.get_rect().width + whitespace_size
        for snake in snakes:
            snake_name = snake.get_name()
            if score is None:
                snake_score = 0
            else:
                snake_score = score[snake_name]
            text_surface = my_font.render(str(snake_score), True, snake.get_color())
            text_surface_copy = text_surface.copy()
            text_surface_copy.fill((0, 0, 0))
            surface.blit(text_surface_copy, (cur_x_coord, 0))
            surface.blit(text_surface, (cur_x_coord, 0))
            cur_x_coord += text_surface.get_rect().width + whitespace_size
        pygame.display.update()
        return

    def game_over(self, winners):
        cell_width = int(c.screen_width / max(self.height, self.width))
        n = self.height * cell_width
        m = self.width * cell_width
        surface = pygame.display.set_mode((m, n))
        surface.fill(pygame.Color('black'))
        font_size1 = min(n, m) // 8
        font1 = pygame.font.SysFont('Arial', font_size1)
        text1 = font1.render('GAME OVER', True, (255, 0, 0))
        text1_rect = text1.get_rect(center=(m // 2, (n * 3) // 8))
        surface.blit(text1, text1_rect)

        font_size2 = min(n, m) // 24
        font2 = pygame.font.SysFont('Arial', font_size2)

        text2 = font2.render(winners['winners'][0], True, (0, 255, 0))
        text2_rect = text2.get_rect()
        text2_rect.midright = (m // 2, (n * 3) // 8 + text1_rect.height)
        surface.blit(text2, text2_rect)

        text3 = font2.render(' won!', True, (255, 255, 255))
        text3_rect = text3.get_rect()
        text3_rect.midleft = (m // 2, (n * 3) // 8 + text1_rect.height)
        surface.blit(text3, text3_rect)

        pygame.display.update()
        return