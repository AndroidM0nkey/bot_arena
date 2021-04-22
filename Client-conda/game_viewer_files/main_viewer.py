from bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object

from game_viewer_files.apple import Apple
from game_viewer_files.snake_body_peace import SnakeBodyPeace
from game_viewer_files.snake import Snake
import game_viewer_files.config as c
import pygame


def invert(p: int, field_height: int):
    return field_height - 1 - p


def get_message_and_display(cur_state: FieldState, field_height: int, field_width: int):
    cell_width = int(c.screen_width / max(field_height, field_width))
    surface = pygame.display.set_mode((field_width * cell_width, field_height * cell_width))
    player_colors = [(0, 255, 0), (0, 0, 255)]  # GREEN and BLUE
    colors_cnt = -1
    surface.fill(pygame.Color('black'))
    for snake_state in cur_state.snakes.values():
        colors_cnt += 1
        snake_peaces = []
        cur_x = snake_state.head.x * cell_width
        cur_y = invert(snake_state.head.y, field_height) * cell_width
        snake_peaces.append(SnakeBodyPeace(cur_x, cur_y, cell_width, player_colors[colors_cnt]))
        for peace in snake_state.tail:
            if peace == Direction.UP():
                cur_y -= cell_width
            if peace == Direction.DOWN():
                cur_y += cell_width
            if peace == Direction.LEFT():
                cur_x -= cell_width
            if peace == Direction.RIGHT():
                cur_x += cell_width
            snake_peaces.append(SnakeBodyPeace(cur_x, cur_y, cell_width, player_colors[colors_cnt]))
        cur_snake = Snake(snake_peaces)
        cur_snake.draw(surface)
    for i in range(len(cur_state.objects)):
        apple = Apple(cur_state.objects[i][0].x * cell_width, invert(cur_state.objects[i][0].y, field_height) *
                      cell_width, cell_width // 2)
        apple.draw(surface)
    pygame.display.update()
    return
