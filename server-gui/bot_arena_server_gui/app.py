import asyncio
import math
from dataclasses import dataclass
from subprocess import PIPE
from threading import Thread, Lock
from typing import List, Iterable, Tuple, Any, Optional

from adt import adt, Case

import gi  # type: ignore
gi.require_version('GLib', '2.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib as glib  # type: ignore
from gi.repository import Gdk as gdk    # type: ignore
from gi.repository import Gtk as gtk    # type: ignore


def optional(T: type, value: str) -> Any:
    x = T(value)
    if x < 0:
        return None
    return x


@adt
class Message:
    SERVER_STARTED: Case
    SERVER_STOPPED: Case


class TitleWidget:
    def __init__(self, app: 'App') -> None:
        self.app = app
        self.label = gtk.Label()
        self.label.set_markup('<span size="12000"><b>Pythons Server</b></span>')
        self.label.set_use_markup(True)

    def root_widget(self) -> gtk.Label:
        return self.label

    def on_message(self, _msg: Message) -> None:
        pass


class StatusWidget:
    def __init__(self, app: 'App') -> None:
        self.app = app
        self.label = gtk.Label()
        self.update_markup(is_server_running=False)

    def on_message(self, msg: Message) -> None:
        is_server_running = msg.match(
            server_started = lambda: True,
            server_stopped = lambda: False,
        )

        self.update_markup(is_server_running)

    def update_markup(self, is_server_running: bool) -> None:
        self.label.set_markup(self.make_markup(is_server_running))

    @staticmethod
    def make_markup(is_server_running: bool) -> str:
        color = 'green' if is_server_running else 'red'
        text = 'Running' if is_server_running else 'Stopped'
        return f'<span size="12000">Status: <span foreground="{color}">{text}</span></span>'

    def root_widget(self) -> gtk.Label:
        return self.label


class ControlButtonWidget:
    def __init__(self, app: 'App') -> None:
        self.app = app
        self.button = gtk.Button()
        self.button.connect('clicked', lambda _: self.on_click())
        self._is_server_running = False
        self.update()

    def on_click(self) -> None:
        if self._is_server_running:
            self.app.stop_server()
        else:
            self.app.start_server()

    def on_message(self, msg: Message) -> None:
        self._is_server_running = msg.match(
            server_started = lambda: True,
            server_stopped = lambda: False,
        )

        self.update()

    def update(self) -> None:
        self.button.set_label(self.make_label())

    def make_label(self) -> str:
        if self._is_server_running:
            return 'Stop'
        else:
            return 'Start'

    def root_widget(self) -> gtk.Button:
        return self.button


class LogSpace:
    def __init__(self, app: 'App') -> None:
        self.app = app

        self.text_view = gtk.TextView()
        self.text_view.set_monospace(True)
        self.text_view.set_editable(False)
        self.log_buf = self.text_view.get_buffer()

        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.add_with_viewport(self.text_view)

        self.frame = gtk.Frame.new('Server logs')
        self.frame.add(self.scrolled_window)
        self.frame.set_margin_left(5)
        self.frame.set_margin_right(5)
        self.frame.set_margin_bottom(5)

        self.text_view.connect('size-allocate', self.scroll_to_the_end)

        self.append_to_log('Server logs will be displayed here...')

    def scroll_to_the_end(self, widget, *args) -> None:
        # Many thanks to https://stackoverflow.com/a/5235358.
        adjustment = self.scrolled_window.get_vadjustment()
        adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())

    def on_message(self, msg: Message) -> None:
        msg.match(
            server_started = self.clear_logs,
            server_stopped = lambda: None,
        )

    def clear_logs(self) -> None:
        self.log_buf.set_text('')

    def append_to_log(self, text: str) -> None:
        end_iter = self.log_buf.get_end_iter()
        self.log_buf.insert(end_iter, text)

    def root_widget(self) -> gtk.Frame:
        return self.frame


class TopRow:
    def __init__(self, app: 'App') -> None:
        self.app = app
        self.title = TitleWidget(app)
        self.status = StatusWidget(app)
        self.control_button = ControlButtonWidget(app)

        self.box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=20)
        self.box.set_margin_left(5)
        self.box.set_margin_right(5)
        self.box.set_margin_top(5)

        self.box.pack_start(self.title.root_widget(), expand=False, fill=False, padding=0)
        self.box.pack_start(self.status.root_widget(), expand=False, fill=False, padding=0)
        self.box.pack_end(self.control_button.root_widget(), expand=False, fill=False, padding=0)

    def on_message(self, msg: Message) -> None:
        self.title.on_message(msg)
        self.status.on_message(msg)
        self.control_button.on_message(msg)

    def root_widget(self) -> gtk.Box:
        return self.box


class BasicParamsTab:
    def __init__(self, app: 'App') -> None:
        self.app = app

        self.listen_address_label = gtk.Label('Listen on:')
        self.listen_address_entry = gtk.Entry()
        self.listen_address_entry.set_text('0.0.0.0')

        self.listen_port_label = gtk.Label('Port:')
        self.listen_port_entry = gtk.Entry()
        self.listen_port_entry.set_input_purpose(gtk.InputPurpose.DIGITS)
        self.listen_port_entry.set_text('23456')

        self.box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=0)

        self.box.pack_start(self.listen_address_label, expand=False, fill=False, padding=0)
        self.box.pack_start(self.listen_address_entry, expand=False, fill=False, padding=20)
        self.box.pack_start(self.listen_port_label, expand=False, fill=False, padding=0)
        self.box.pack_start(self.listen_port_entry, expand=False, fill=False, padding=20)

        self.box.set_margin_top(5)
        self.box.set_margin_bottom(5)
        self.box.set_margin_left(5)
        self.box.set_margin_right(5)

        self.outer_box = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=0)
        self.outer_box.pack_start(self.box, expand=False, fill=False, padding=0)

    def on_message(self, msg: Message) -> None:
        is_server_running = msg.match(
            server_started = lambda: True,
            server_stopped = lambda: False,
        )

        self.listen_address_entry.set_sensitive(not is_server_running)
        self.listen_port_entry.set_sensitive(not is_server_running)

    def root_widget(self) -> gtk.Box:
        return self.outer_box

    def get_startup_params(self) -> 'BasicStartupParams':
        address = self.listen_address_entry.get_text()
        try:
            port = int(self.listen_port_entry.get_text())
        except ValueError:
            raise ValueError('Port must be an integer number')
        return BasicStartupParams(address, port)


lots = 1e+10

class ExtendedParamsTab:
    def __init__(self, app: 'App') -> None:
        self.app = app

        self.max_client_name_len_label = gtk.Label('Maximum allowed client name length:')
        self.max_client_name_len_input = gtk.SpinButton.new_with_range(0, lots, 1)
        self.max_client_name_len_input.set_value(50)

        self.min_field_side_label = gtk.Label('Minimum allowed field side (width & height):')
        self.min_field_side_input = gtk.SpinButton.new_with_range(0, lots, 1)
        self.min_field_side_input.set_value(5)
        self.min_field_side_input.connect('value-changed', self.update_max_field_side)

        self.max_field_side_label = gtk.Label('Maximum allowed field side (width & height):')
        self.max_field_side_input = gtk.SpinButton.new_with_range(0, lots, 1)
        self.max_field_side_input.set_value(200)
        self.max_field_side_input.connect('value-changed', self.update_min_field_side)

        self.max_food_items_label = gtk.Label('Maximum allowed initial number of food items:')
        self.max_food_items_input = gtk.SpinButton.new_with_range(0, lots, 1)
        self.max_food_items_input.set_value(50)

        self.max_password_len_label = gtk.Label('Maximum allowed password length:')
        self.max_password_len_input = gtk.SpinButton.new_with_range(0, lots, 1)
        self.max_password_len_input.set_value(500)

        self.max_room_name_len_label = gtk.Label('Maximum allowed room name length:')
        self.max_room_name_len_input = gtk.SpinButton.new_with_range(16, lots, 1)
        self.max_room_name_len_input.set_value(50)

        self.max_room_players_label = gtk.Label('Maximum allowed number of players in a room:')
        self.max_room_players_input = gtk.SpinButton.new_with_range(0, lots, 1)
        self.max_room_players_input.set_value(20)

        self.max_snake_len_label = gtk.Label('Maximum allowed initial snake length:')
        self.max_snake_len_input = gtk.SpinButton.new_with_range(0, lots, 1)
        self.max_snake_len_input.set_value(50)

        self.max_turn_timeout_label = gtk.Label('Maximum allowed turn timeout in seconds (-1 for no limit):')
        self.max_turn_timeout_input = gtk.SpinButton.new_with_range(-1, lots, 1)
        self.max_turn_timeout_input.set_value(-1)

        self.max_turns_label = gtk.Label('Maximum allowed number of turns (-1 for no limit):')
        self.max_turns_input = gtk.SpinButton.new_with_range(-1, lots, 1)
        self.max_turns_input.set_value(-1)

        self.turn_delay_label = gtk.Label('Delay between turns in seconds (0 for no delay):')
        self.turn_delay_input = gtk.SpinButton.new_with_range(0, lots, 0.001)
        self.turn_delay_input.set_value(0.1)

        self.work_units_label = gtk.Label('Maximum amount of work done generating field:')
        self.work_units_input = gtk.SpinButton.new_with_range(0, lots, 10)
        self.work_units_input.set_value(500)

        self.grid = gtk.Grid()

        rows = [0, 0]
        for label, input, col in self.inputs():
            label_box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=0)
            label_box.pack_end(label, expand=False, fill=False, padding=0)
            self.grid.attach(label_box, left=2*col, top=rows[col], width=1, height=1)
            self.grid.attach(input, left=1+2*col, top=rows[col], width=1, height=1)
            rows[col] += 1

        self.grid.set_row_spacing(5)
        self.grid.set_column_spacing(20)
        self.grid.set_margin_top(5)
        self.grid.set_margin_bottom(5)
        self.grid.set_margin_left(5)
        self.grid.set_margin_right(5)

    def update_max_field_side(self, *args) -> None:
        min_value = self.min_field_side_input.get_value()
        max_value = self.max_field_side_input.get_value()
        if min_value > max_value:
            self.max_field_side_input.set_value(min_value)

    def update_min_field_side(self, *args) -> None:
        min_value = self.min_field_side_input.get_value()
        max_value = self.max_field_side_input.get_value()
        if max_value < min_value:
            self.min_field_side_input.set_value(max_value)

    def inputs(self) -> Iterable[Tuple[gtk.Label, gtk.Widget, int]]:
        yield (self.max_client_name_len_label, self.max_client_name_len_input, 0)
        yield (self.min_field_side_label, self.min_field_side_input, 0)
        yield (self.max_field_side_label, self.max_field_side_input, 0)
        yield (self.max_food_items_label, self.max_food_items_input, 0)
        yield (self.max_password_len_label, self.max_password_len_input, 0)
        yield (self.max_room_name_len_label, self.max_room_name_len_input, 0)
        yield (self.max_room_players_label, self.max_room_players_input, 1)
        yield (self.max_snake_len_label, self.max_snake_len_input, 1)
        yield (self.max_turn_timeout_label, self.max_turn_timeout_input, 1)
        yield (self.max_turns_label, self.max_turns_input, 1)
        yield (self.turn_delay_label, self.turn_delay_input, 1)
        yield (self.work_units_label, self.work_units_input, 1)

    def on_message(self, msg: Message) -> None:
        is_server_running = msg.match(
            server_started = lambda: True,
            server_stopped = lambda: False
        )

        for _, input, _ in self.inputs():
            input.set_sensitive(not is_server_running)

    def root_widget(self) -> gtk.Box:
        return self.grid

    def get_startup_params(self) -> 'ExtendedStartupParams':
        return ExtendedStartupParams(
            max_client_name_len = int(self.max_client_name_len_input.get_value()),
            min_field_side = int(self.min_field_side_input.get_value()),
            max_field_side = int(self.max_field_side_input.get_value()),
            max_food_items = int(self.max_food_items_input.get_value()),
            max_password_len = int(self.max_password_len_input.get_value()),
            max_room_name_len = int(self.max_room_name_len_input.get_value()),
            max_room_players = int(self.max_room_players_input.get_value()),
            max_snake_len = int(self.max_snake_len_input.get_value()),
            max_turn_timeout = optional(float, self.max_turn_timeout_input.get_value()),
            max_turns = optional(int, self.max_turns_input.get_value()),
            turn_delay = int(self.turn_delay_input.get_value()),
            work_units = int(self.work_units_input.get_value()),
        )


class ParamsRow:
    def __init__(self, app: 'App') -> None:
        self.app = app

        self.basic_tab = BasicParamsTab(app)
        self.extended_tab = ExtendedParamsTab(app)

        self.notebook = gtk.Notebook()
        self.notebook.append_page(self.basic_tab.root_widget(), gtk.Label('Basic parameters'))
        self.notebook.append_page(self.extended_tab.root_widget(), gtk.Label('Extended parameters'))

        self.notebook.set_margin_left(5)
        self.notebook.set_margin_right(5)

    def on_message(self, msg: Message) -> None:
        self.basic_tab.on_message(msg)
        self.extended_tab.on_message(msg)

    def root_widget(self) -> gtk.Notebook:
        return self.notebook

    def get_startup_params(self) -> 'StartupParams':
        return StartupParams(
            basic = self.basic_tab.get_startup_params(),
            extended = self.extended_tab.get_startup_params(),
        )


class LayoutColumn:
    def __init__(self, app: 'App'):
        self.app = app
        self.top_row = TopRow(app)
        self.params_row = ParamsRow(app)
        self.log_space = LogSpace(app)

        self.box = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)

        self.box.pack_start(self.top_row.root_widget(), expand=False, fill=False, padding=0)
        self.box.pack_start(self.params_row.root_widget(), expand=False, fill=False, padding=0)
        self.box.pack_end(self.log_space.root_widget(), expand=True, fill=True, padding=0)

    def on_message(self, msg: Message) -> None:
        self.top_row.on_message(msg)
        self.params_row.on_message(msg)
        self.log_space.on_message(msg)

    def root_widget(self) -> gtk.Box:
        return self.box


@dataclass
class BasicStartupParams:
    listen_address: str
    listen_port: int

    def get_args(self) -> List[str]:
        return ['--listen-on', self.listen_address, '--port', str(self.listen_port)]


@dataclass
class ExtendedStartupParams:
    max_client_name_len: int
    min_field_side: int
    max_field_side: int
    max_food_items: int
    max_password_len: int
    max_room_name_len: int
    max_room_players: int
    max_snake_len: int
    max_turn_timeout: Optional[float]
    max_turns: Optional[int]
    turn_delay: int
    work_units: int

    def get_args(self) -> List[str]:
        return [
            '--max-client-name-len', str(self.max_client_name_len),
            '--min-field-side', str(self.min_field_side),
            '--max-field-side', str(self.max_field_side),
            '--max-food-items', str(self.max_food_items),
            '--max-password-len', str(self.max_password_len),
            '--max-room-name-len', str(self.max_room_name_len),
            '--max-room-players', str(self.max_room_players),
            '--max-snake-len', str(self.max_snake_len),
            '--turn-delay', str(self.turn_delay),
            '--work-units', str(self.work_units),
        ] + (
            [] if self.max_turn_timeout is None else ['--max-turn-timeout', str(self.max_turn_timeout)]
        ) + (
            [] if self.max_turns is None else ['--max-turns', str(self.max_turns)]
        )


@dataclass
class StartupParams:
    basic: BasicStartupParams
    extended: ExtendedStartupParams

    def get_args(self) -> List[str]:
        return self.basic.get_args() + self.extended.get_args()


class App:
    def __enter__(self) -> None:
        pass

    def __exit__(self, *args) -> None:
        try:
            self._server_thread.force_stop()
        except ProcessLookupError:
            pass

    def __init__(self) -> None:
        self._server_thread = ServerThread(self)

    def on_activate(self, app: gtk.Application) -> None:
        self.window = gtk.ApplicationWindow(application=app)
        self.window.resize(800, 600)
        self.layout_column = LayoutColumn(self)
        self.window.add(self.layout_column.root_widget())
        self.window.show_all()

    def raise_message(self, msg: Message) -> None:
        self.layout_column.on_message(msg)

    def start_server(self) -> None:
        try:
            self._server_thread.start()
        except Exception as e:
            dialog = gtk.MessageDialog(
                parent = self.window,
                message_type = gtk.MessageType.ERROR,
                buttons = gtk.ButtonsType.OK,
            )
            dialog.set_markup(f'Error: {e}')
            dialog.set_modal(True)
            dialog.run()
            dialog.hide()
            return

        self.raise_message(Message.SERVER_STARTED())

    def on_server_stopped(self) -> None:
        self.append_to_log('\n--- Server stopped ---')
        self.raise_message(Message.SERVER_STOPPED())

    def stop_server(self) -> None:
        self._server_thread.force_stop()

    def append_to_log(self, text: str) -> None:
        self.layout_column.log_space.append_to_log(text)

    def get_startup_params(self) -> StartupParams:
        return self.layout_column.params_row.get_startup_params()


class ServerThread:
    def __init__(self, app: App):
        self.app = app
        self._running = False
        self._dead = True
        self._lock = Lock()
        self.child = None

    def set_dead(self, is_dead: bool) -> None:
        with self._lock:
            self._dead = is_dead

    def is_dead(self) -> bool:
        with self._lock:
            return self._dead

    def set_running(self, is_running: bool) -> None:
        with self._lock:
            self._running = is_running

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self) -> None:
        if self._running:
            raise Exception('Attempted to start more than one server instance')

        params = self.app.get_startup_params()

        self.set_dead(False)
        thread = Thread(target = lambda: self.run(params), daemon=True)
        thread.start()

    def run(self, params: StartupParams) -> None:
        asyncio.run(self.async_run(params))
        self.set_running(False)
        self.child = None
        gdk.threads_add_idle(glib.PRIORITY_HIGH_IDLE, self.app.on_server_stopped)

    async def async_run(self, params: StartupParams) -> None:
        self.child = await asyncio.create_subprocess_exec(
            'bot-arena-server',
            *params.get_args(),
            stdout=PIPE,
            stderr=PIPE,
        )

        await asyncio.gather(
            self.log_relay(self.child.stdout),
            self.log_relay(self.child.stderr),
            self.process_awaiter(),
        )

    async def log_relay(self, stream: asyncio.StreamReader) -> None:
        while not self.is_dead():
            data = (await stream.readline()).decode()
            if len(data) == 0:
                break
            gdk.threads_add_idle(glib.PRIORITY_HIGH_IDLE, self.app.append_to_log, data)

    async def process_awaiter(self) -> None:
        await self.child.wait()
        self.set_dead(True)

    def force_stop(self) -> None:
        if self.child is None:
            raise ProcessLookupError()

        self.child.terminate()


def main() -> None:
    app = App()
    with app:
        gtk_app = gtk.Application()
        gtk_app.connect('activate', app.on_activate)
        gtk_app.run(None)
