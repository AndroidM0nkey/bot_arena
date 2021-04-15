from bot_arena_proto.data import *
from bot_arena_proto.event import Event
from bot_arena_proto.session import ClientSession, ClientInfo

from game_viewer.apple import Apple
from game_viewer.snake_body_peace import SnakeBodyPeace
from game_viewer.snake import Snake
import game_viewer.config as c
import pygame
from pygame_textinput import TextInput
import pygame.locals as pl
import curio


def get_message_and_display(cur_state: FieldState):
    global main_surface
    player_colors = [(0, 255, 0), (0, 0, 255)]  # GREEN and BLUE
    colors_cnt = -1
    main_surface.fill(pygame.Color('black'))
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
        cur_snake.draw(main_surface)
    apple = Apple(cur_state.objects[0][0].x * c.cell_width, cur_state.objects[0][0].y * c.cell_width)
    apple.draw(main_surface)
    pygame.display.update()
    return


def get_user_input(initial_string: str) -> str:
    global main_surface
    textinput = TextInput(initial_string=initial_string)
    clock = pygame.time.Clock()
    ans = ""
    ended = False
    while True:
        main_surface.fill((225, 225, 225))
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pl.K_RETURN:
                ans = textinput.get_text()[len(initial_string):]
                main_surface.fill((0, 0, 0))
                pygame.display.update()
                ended = True
                break
            if event.type == pygame.QUIT:
                exit()
        if ended:
            break
        textinput.update(events)
        main_surface.blit(textinput.get_surface(), (10, 10))
        pygame.display.update()
        clock.tick(30)
    return ans


sess = None
main_surface = None


async def main():
    global sess
    global main_surface
    pygame.init()
    main_surface = pygame.display.set_mode((c.screen_width, c.screen_width))
    pygame.display.set_caption('Pythons')
    server = get_user_input("Введите адрес хоста: ")
    port = get_user_input("Введите порт: ")
    # Connect to the server
    socket = await curio.open_connection(host=server, port=int(port))

    # We need an object with read/write methods. In curio, sockets have
    # recv/send methods, and streams have read/write methods. Hence, we need
    # to convert the socket to a stream. Consult the documentation
    # (https://curio.readthedocs.io/en/latest/reference.html#networking)
    # for details.
    stream = socket.as_stream()

    # [[[ Interesting things start here ]]]

    # Create a ClientSession
    client_info = ClientInfo(name='@viewer')
    sess = ClientSession(stream=stream, client_info=client_info)

    # Perform the handshake
    await sess.initialize()

    ...  # Do what you want before being ready to enter a game

    # Start the game
    await sess.ready()
    game_info = await sess.wait_until_game_started()

    # Important data
    field_width = game_info.field_width
    field_height = game_info.field_height
    main_surface = pygame.display.set_mode((c.cell_width * field_width, c.cell_width * field_height))

    # Handle server-sent notifications
    while True:
        notification = await sess.wait_for_notification()

        # Handle the notification. See the documentation for the
        # `algebraic-data-type` package.
        #
        # Note: the functions `take_turn`, `handle_new_field_state`, `handle_event`
        # and `handle_error` are async, and the result of the `.match()` method
        # is awaited. This is correct and probably the only way to combine pattern
        # matching with asynchronous IO because the following actually happens:
        #
        # (1) `.match()` method calls (but does not await) one of these four functions.
        # (2) This function returns a `coroutine` object, which can be awaited.
        # (3) This object is the value returned from `.match()`.
        # (4) This object is then awaited.
        await notification.match(
            request=None,
            field_state=handle_new_field_state,
            event=handle_event,
            error=handle_error,
        )
    # Test:
    print(server)
    print(port)
    test_snakes = {'Bob': SnakeState(Point(1, 2), [Direction.DOWN(), Direction.DOWN(), Direction.RIGHT(),
                                                   Direction.RIGHT(), Direction.UP()]),
                   'Alice': SnakeState(Point(2, 11), [Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(),
                                                      Direction.DOWN(), Direction.DOWN(), Direction.LEFT(),
                                                      Direction.DOWN(), Direction.DOWN(), Direction.RIGHT(),
                                                      Direction.RIGHT(), Direction.RIGHT(), Direction.RIGHT(),
                                                      Direction.RIGHT(), Direction.UP()])}
    test_objects = [(Point(7, 11), Object.FOOD())]
    get_message_and_display(FieldState(test_snakes, test_objects))
    pygame.time.wait(5000)


async def handle_new_field_state(state):
    global main_surface
    # Do something when a new field state arrives.
    get_message_and_display(state)
    print(f'New field state: {state}')


async def handle_event(event):
    # Do something when an event happens.
    print(f'Event happened: {event}')


async def handle_error(description):
    # Do something when an error happens.
    print(f'Error: {description}')
    exit()


if __name__ == '__main__':
    curio.run(main)
