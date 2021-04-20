from bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object

from game_viewer_files.apple import Apple
from game_viewer_files.snake_body_peace import SnakeBodyPeace
from game_viewer_files.snake import Snake
import game_viewer_files.config as c
import pygame


def invert(p: int):
    return (c.screen_width / c.cell_width) - 1 - p


def get_message_and_display(cur_state: FieldState, surface: pygame.display):
    player_colors = [(0, 255, 0), (0, 0, 255)]  # GREEN and BLUE
    colors_cnt = -1
    surface.fill(pygame.Color('black'))
    for snake_state in cur_state.snakes.values():
        colors_cnt += 1
        snake_peaces = []
        cur_x = snake_state.head.x * c.cell_width
        cur_y = invert(snake_state.head.y) * c.cell_width
        snake_peaces.append(SnakeBodyPeace(cur_x, cur_y, player_colors[colors_cnt]))
        for peace in snake_state.tail:
            if peace == Direction.UP():
                cur_y -= c.cell_width
            if peace == Direction.DOWN():
                cur_y += c.cell_width
            if peace == Direction.LEFT():
                cur_x -= c.cell_width
            if peace == Direction.RIGHT():
                cur_x += c.cell_width
            snake_peaces.append(SnakeBodyPeace(cur_x, cur_y, player_colors[colors_cnt]))
        cur_snake = Snake(snake_peaces)
        cur_snake.draw(surface)
    for i in range(len(cur_state.objects)):
        apple = Apple(cur_state.objects[i][0].x * c.cell_width, invert(cur_state.objects[i][0].y) * c.cell_width)
        apple.draw(surface)
    pygame.display.update()
    return