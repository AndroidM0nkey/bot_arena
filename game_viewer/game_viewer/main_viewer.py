from bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object

from game_viewer.apple import Apple
from game_viewer.snake_body_peace import SnakeBodyPeace
from game_viewer.snake import Snake
import game_viewer.config as c
import pygame


def get_message_and_display(cur_state: FieldState, surface: pygame.display):
    player_colors = [(0, 255, 0), (0, 0, 255)]  # GREEN and BLUE
    colors_cnt = -1
    surface.fill(pygame.Color('black'))
    for snake_state in cur_state.snakes.values():
        colors_cnt += 1
        snake_peaces = []
        cur_x = snake_state.head.x * c.cell_width
        cur_y = snake_state.head.y * c.cell_width
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
    apple = Apple(cur_state.objects[0][0].x * c.cell_width, cur_state.objects[0][0].y * c.cell_width)
    apple.draw(surface)
    pygame.display.update()
    return


def main():
    pygame.init()
    main_surface = pygame.display.set_mode((c.screen_width, c.screen_width))
    pygame.display.set_caption('Pythons')
    # Test:
    test_snakes = {'Bob': SnakeState(Point(1, 2), [Direction.DOWN(), Direction.DOWN(), Direction.RIGHT(), Direction.RIGHT(),
                                                   Direction.UP()]),
                   'Alice': SnakeState(Point(2, 11), [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(), Direction.DOWN(),
                                                      Direction.DOWN(), Direction.LEFT(), Direction.DOWN(), Direction.DOWN(),
                                                      Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(),
                                                      Direction.RIGHT(), Direction.UP()])}
    test_objects = [(Point(7, 11), Object.FOOD())]
    get_message_and_display(FieldState(test_snakes, test_objects), main_surface)
    pygame.time.wait(10000)


if __name__ == '__main__':
    main()
