import asyncio
from dataclasses import dataclass
from subprocess import PIPE
from threading import Thread, Lock
from typing import Iterable

from adt import adt, Case

import gi
gi.require_version('GLib', '2.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib as glib
from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk


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

        self.append_to_log('Server logs will be displayed here...')

    def on_message(self, msg: Message) -> None:
        msg.match(
            server_started = self.clear_logs,
            server_stopped = lambda: None,
        )

    def clear_logs(self) -> None:
        self.log_buf.set_text('')

    def append_to_log(self, text: str) -> None:
        self.log_buf.insert_at_cursor(text)

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


class LayoutColumn:
    def __init__(self, app: 'App'):
        self.app = app
        self.top_row = TopRow(app)
        self.log_space = LogSpace(app)

        self.box = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)

        self.box.pack_start(self.top_row.root_widget(), expand=False, fill=False, padding=0)
        self.box.pack_end(self.log_space.root_widget(), expand=True, fill=True, padding=0)

    def on_message(self, msg: Message) -> None:
        self.top_row.on_message(msg)
        self.log_space.on_message(msg)

    def root_widget(self) -> gtk.Box:
        return self.box


@dataclass
class StartupParams:
    listen_address: str
    listen_port: int


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
        self._server_thread.start()
        self.raise_message(Message.SERVER_STARTED())

    def on_server_stopped(self) -> None:
        self.append_to_log('--- Server stopped ---')
        self.raise_message(Message.SERVER_STOPPED())

    def stop_server(self) -> None:
        self._server_thread.force_stop()

    def append_to_log(self, text: str) -> None:
        self.layout_column.log_space.append_to_log(text)


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

    def start(self):
        if self._running:
            raise Exception('Attempted to start more than one server instance')
        self.set_dead(False)

        thread = Thread(target=self.run, daemon=True)
        thread.start()

    def run(self):
        asyncio.run(self.async_run())
        self.set_running(False)
        self.child = None
        gdk.threads_add_idle(glib.PRIORITY_HIGH_IDLE, self.app.on_server_stopped)

    async def async_run(self):
        self.child = await asyncio.create_subprocess_exec(
            'bot-arena-server',
            *self.get_server_args(),
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

    def get_server_args(self) -> Iterable[str]:
        return []


def main() -> None:
    app = App()
    with app:
        gtk_app = gtk.Application()
        gtk_app.connect('activate', app.on_activate)
        gtk_app.run(None)
