import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk


def make_label_markup(running: bool) -> str:
    color = 'green' if running else 'red'
    text = 'Running' if running else 'Stopped'
    return f'<span size="12000">Status: <span foreground="{color}">{text}</span></span>'


def on_activate(app: gtk.Application) -> None:
    window = gtk.ApplicationWindow(application=app)
    window.resize(400, 400)

    column = gtk.Box.new(orientation=gtk.Orientation.VERTICAL, spacing=5)
    top_row = gtk.Box.new(orientation=gtk.Orientation.HORIZONTAL, spacing=20)
    top_row.set_margin_left(5)
    top_row.set_margin_right(5)

    title = gtk.Label.new()
    title.set_markup('<span size="12000">Pythons Server</span>')
    title.set_use_markup(True)
    top_row.pack_start(title, expand=False, fill=False, padding=0)

    status_label = gtk.Label.new()
    status_label.set_markup(make_label_markup(running=False))
    status_label.set_use_markup(True)
    top_row.pack_start(status_label, expand=False, fill=False, padding=0)

    control_button = gtk.Button.new()
    control_button.set_label('Start')
    top_row.pack_end(control_button, expand=False, fill=False, padding=0)

    column.pack_start(top_row, expand=False, fill=False, padding=0)

    log_view = gtk.TextView.new()
    log_view.set_monospace(True)
    log_view.set_editable(False)
    log_buf = log_view.get_buffer()
    with open('bot_arena_server_gui/__main__.py') as f:
        log_buf.insert_at_cursor(f.read())

    log_scroll = gtk.ScrolledWindow.new()
    log_scroll.add_with_viewport(log_view)

    log_frame = gtk.Frame.new('Server logs')
    log_frame.add(log_scroll)
    log_frame.set_margin_left(5)
    log_frame.set_margin_right(5)
    log_frame.set_margin_bottom(5)
    column.pack_end(log_frame, expand=True, fill=True, padding=0)


    window.add(column)
    window.show_all()


def main() -> None:
    app = gtk.Application()
    app.connect('activate', on_activate)
    app.run(None)

if __name__ == '__main__':
    main()
