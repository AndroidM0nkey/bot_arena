from bot_arena_proto.data import FieldState, Direction, SnakeState, Point, Object

from game_viewer.apple import Apple
from game_viewer.snake_body_peace import SnakeBodyPeace
from game_viewer.snake import Snake
import game_viewer.config as c
import pygame
from pygame_textinput import TextInput
import pygame.locals as pl


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


def get_user_input(initial_string: str, surface: pygame.display) -> str:
    textinput = TextInput(initial_string=initial_string)
    clock = pygame.time.Clock()
    ans = ""
    ended = False
    while True:
        surface.fill((225, 225, 225))
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pl.K_RETURN:
                ans = textinput.get_text()[len(initial_string):]
                surface.fill((0, 0, 0))
                pygame.display.update()
                ended = True
                break
            if event.type == pygame.QUIT:
                exit()
        if ended:
            break
        textinput.update(events)
        surface.blit(textinput.get_surface(), (10, 10))
        pygame.display.update()
        clock.tick(30)
    return ans


def main():
    pygame.init()
    main_surface = pygame.display.set_mode((c.screen_width, c.screen_width))
    pygame.display.set_caption('Pythons')
    server = get_user_input("Введите адрес сервера: ", main_surface)
    port = get_user_input("Введите порт: ", main_surface)
    # Test:
    print(server)
    print(port)
    test_snakes = {'Bob': SnakeState(Point(1, 2), [Direction.DOWN(), Direction.DOWN(), Direction.RIGHT(), Direction.RIGHT(),
                                                   Direction.UP()]),
                   'Alice': SnakeState(Point(2, 11), [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(), Direction.DOWN(),
                                                      Direction.DOWN(), Direction.LEFT(), Direction.DOWN(), Direction.DOWN(),
                                                      Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(),
                                                      Direction.RIGHT(), Direction.UP()])}
    test_objects = [(Point(7, 11), Object.FOOD())]
    get_message_and_display(FieldState(test_snakes, test_objects), main_surface)
    pygame.time.wait(5000)


if __name__ == '__main__':
    main()
