# =====================================================
#        Authors Brad Heffernan and Erik Dubois
# =====================================================

import cairo
import gi
import shutil
import GUI
import Modal
import Functions as fn
import threading
import signal

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Wnck', '3.0')

from gi.repository import Gtk, GdkPixbuf, Gdk, Wnck, GLib, GdkX11  # noqa


class TransparentWindow(Gtk.Window):
    cmd_shutdown = "systemctl poweroff"
    cmd_restart = "systemctl reboot"
    cmd_suspend = "systemctl suspend"
    cmd_hibernate = "systemctl hibernate"
    cmd_lock = 'betterlockscreen -l dim -- --time-str="%H:%M"'
    wallpaper = "/usr/share/arcologout/wallpaper.jpg"
    d_buttons = ['cancel',
                 'shutdown',
                 'restart',
                 'suspend',
                 'hibernate',
                 'lock',
                 'logout']
    binds = {'lock': 'K',
             'restart': 'R',
             'shutdown': 'S',
             'suspend': 'U',
             'hibernate': 'H',
             'logout': 'L',
             'cancel': 'Escape',
             'settings': 'P'}
    commands = {
        'lock': cmd_lock,
        'restart': cmd_restart,
        'shutdown': cmd_shutdown,
        'suspend': cmd_suspend,
        'hibernate': cmd_hibernate,
        'logout': fn._get_logout()
    }
    theme = "white"
    hover = "#ffffff"
    icon = 64
    font = 11
    buttons = None
    active = False
    opacity = 0.8

    def __init__(self):
        super(TransparentWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL, title="Arcolinux Logout")
        # Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL)
        # self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_above(True)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(300, 220)
        self.connect('delete-event', self.on_close)
        self.connect('destroy', self.on_close)
        self.connect('draw', self.draw)
        self.connect("key-press-event", self.on_keypress)
        self.connect("window-state-event", self.on_window_state_event)
        self.set_decorated(False)

        # self.monitor = 0

        if not fn.os.path.isdir(fn.home + "/.config/arcologout"):
            fn.os.mkdir(fn.home + "/.config/arcologout")

        if not fn.os.path.isfile(fn.home + "/.config/arcologout/arcologout.conf"):
            shutil.copy(fn.root_config, fn.home + "/.config/arcologout/arcologout.conf")


        # s = Gdk.Screen.get_default()
        # self.width = s.width()
        # height = s.height()

        # screens = Gdk.Display.get_default()
        # s = screens.get_n_monitors()

        self.width = 0
        # for x in range(s):
        #     sc = screens.get_monitor(x)
        #     rec = sc.get_geometry()
        #     self.width += rec.width

        screen = self.get_screen()

        # monitor = screens.get_monitor(0)
        # rect = monitor.get_geometry()

        # self.single_width = rect.width
        # height = rect.height

        # self.move(0, 0)
        # self.resize(self.width, height)

        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        fn.get_config(self, Gdk, Gtk, fn.config)

        if self.buttons is None or self.buttons == ['']:
            self.buttons = self.d_buttons

        self.fullscreen()
        self.set_app_paintable(True)
        self.present()

        GUI.GUI(self, Gtk, GdkPixbuf, fn.working_dir, fn.os, Gdk, fn)
        if not fn.os.path.isfile("/tmp/arcologout.lock"):
            with open("/tmp/arcologout.lock", "w") as f:
                f.write("")

    def on_save_clicked(self, widget):
        try:
            with open(fn.home + "/.config/arcologout/arcologout.conf", "r") as f:
                lines = f.readlines()
                f.close()

            pos_opacity = fn._get_position(lines, "opacity")
            pos_size = fn._get_position(lines, "icon_size")
            pos_theme = fn._get_position(lines, "theme=")
            pos_font = fn._get_position(lines, "font_size=")

            lines[pos_opacity] = "opacity=" + str(int(self.hscale.get_value())) + "\n"
            lines[pos_size] = "icon_size=" + str(int(self.icons.get_value())) + "\n"
            lines[pos_theme] = "theme=" + self.themes.get_active_text() + "\n"
            lines[pos_font] = "font_size=" + str(int(self.fonts.get_value())) + "\n"

            with open(fn.home + "/.config/arcologout/arcologout.conf", "w") as f:
                f.writelines(lines)
                f.close()
            self.popover.popdown()
        except Exception as e:
            fn.os.unlink(fn.home + "/.config/arcologout/arcologout.conf")
            if not fn.os.path.isfile(fn.home + "/.config/arcologout/arcologout.conf"):
                shutil.copy(fn.root_config, fn.home + "/.config/arcologout/arcologout.conf")
            with open(fn.home + "/.config/arcologout/arcologout.conf", "r") as f:
                lines = f.readlines()
                f.close()

            pos_opacity = fn._get_position(lines, "opacity")
            pos_size = fn._get_position(lines, "icon_size")
            pos_theme = fn._get_position(lines, "theme=")
            pos_font = fn._get_position(lines, "font_size=")

            lines[pos_opacity] = "opacity=" + str(int(self.hscale.get_value())) + "\n"
            lines[pos_size] = "icon_size=" + str(int(self.icons.get_value())) + "\n"
            lines[pos_theme] = "theme=" + self.themes.get_active_text() + "\n"
            lines[pos_font] = "font_size=" + str(int(self.fonts.get_value())) + "\n"

            with open(fn.home + "/.config/arcologout/arcologout.conf", "w") as f:
                f.writelines(lines)
                f.close()
            self.popover.popdown()

    def on_mouse_in(self, widget, event, data):
        if data in [self.binds.get(action) for action in self.d_buttons]:
            action = [action for action, key in self.binds.items() if key == data][0]

            pix_buf = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(fn.working_dir, f'themes/{self.theme}/{action}_blur.svg'), self.icon, self.icon)
            self.images.get(action).set_from_pixbuf(pix_buf)

            self.labels.get(action).set_markup(
                f'<span size="{str(self.font)}000" '
                f'foreground="{self.hover}">{action.title()} ({self.binds.get(action)})</span>')

        elif data == self.binds.get('settings'):
            pix_buf = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(fn.working_dir, 'configure_blur.svg'), 48, 48)
            self.imageset.set_from_pixbuf(pix_buf)
        elif data == 'light':
            pix_buf = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(fn.working_dir, 'light_blur.svg'), 48, 48)
            self.imagelig.set_from_pixbuf(pix_buf)
        event.window.set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))

    def on_mouse_out(self, widget, event, data):
        if not self.active:
            if data in [self.binds.get(action) for action in self.d_buttons]:
                action = [action for action, key in self.binds.items() if key == data][0]

                pix_buf = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(fn.working_dir, f'themes/{self.theme}/{action}.svg'), self.icon, self.icon)
                self.images.get(action).set_from_pixbuf(pix_buf)

                self.labels.get(action).set_markup(
                    f'<span size="{str(self.font)}000" '
                    f'foreground="{self.hover}">{action.title()} ({self.binds.get(action)})</span>')

            elif data == self.binds.get('settings'):
                pix_buf = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(fn.working_dir, 'configure.svg'), 48, 48)
                self.imageset.set_from_pixbuf(pix_buf)
            elif data == 'light':
                pix_buf = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(fn.working_dir, 'light.svg'), 48, 48)
                self.imagelig.set_from_pixbuf(pix_buf)

    def on_click(self, widget, event, data):
        self.click_button(widget, data)

    def on_window_state_event(self, widget, ev):
        self.__is_fullscreen = bool(ev.new_window_state & Gdk.WindowState.FULLSCREEN)  # noqa

    def draw(self, widget, context):
        context.set_source_rgba(0, 0, 0, self.opacity)
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)

    def on_keypress(self, widget=None, event=None, data=None):
        shortcut_keys = [self.binds.get('cancel'), self.binds.get('shutdown'), self.binds.get('restart'),
                         self.binds.get('suspend'), self.binds.get('logout'), self.binds.get('lock'),
                         self.binds.get('hibernate'), self.binds.get('settings')]

        for key in shortcut_keys:
            if event.keyval == Gdk.keyval_to_lower(Gdk.keyval_from_name(key)):
                self.click_button(widget, key)

    def click_button(self, widget, data=None):
        if data in [self.binds.get(action) for action in self.d_buttons]:
            action = [action for action, key in self.binds.items() if key == data][0]
            self.active = True
            fn.button_toggled(self, data)
            fn.button_active(self, data, GdkPixbuf)
            if action == 'lock' and not fn.os.path.isdir(fn.home + "/.cache/betterlockscreen"):
                self.betterlockscreen_not_cached()
            command = self.commands.get(action, None)
            execute_command_and_quit(command)

        elif data == self.binds.get('settings'):
            self.themes.grab_focus()
            self.popover.set_relative_to(self.Eset)
            self.popover.show_all()
            self.popover.popup()

        elif data == 'light':
            self.popover2.set_relative_to(self.Elig)
            self.popover2.show_all()
            self.popover2.popup()

    def modal_close(self, widget, signal):
        print(self.state)

    def __exec_cmd(self, cmdline):
        fn.os.system(cmdline)

    def on_close(self, widget, data):
        execute_command_and_quit()

    def message_box(self, message, title):
        md = Gtk.MessageDialog(parent=self,
                               message_type=Gtk.MessageType.INFO,
                               buttons=Gtk.ButtonsType.YES_NO,
                               text=title)
        md.format_secondary_markup(message)  # noqa

        result = md.run()
        md.destroy()

        if result in (Gtk.ResponseType.OK, Gtk.ResponseType.YES):
            return True
        else:
            return False

    def betterlockscreen_not_cached(self):
        if fn.os.path.isfile(self.wallpaper):
            self.lbl_stat.set_markup(
                "<span size=\"x-large\"><b>Caching lockscreen images for a faster locking next time</b></span>")  # noqa
            t = threading.Thread(target=fn.cache_bl,
                                 args=(self, GLib, Gtk,))
            t.daemon = True
            t.start()
        else:
            self.lbl_stat.set_markup(
                "<span size=\"x-large\"><b>Choose a wallpaper with arcolinux-betterlockscreen</b></span>")  # noqa
            self.Ec.set_sensitive(True)
            self.active = False


def __exec_cmd(cmdline):
    fn.os.system(cmdline)


def execute_command_and_quit(command=None):
    fn.os.unlink("/tmp/arcologout.lock")
    fn.os.unlink("/tmp/arcologout.pid")
    if command:
        __exec_cmd(command)
    Gtk.main_quit(0)


def signal_handler(sig, frame):
    print('\narcologout is Closing.')
    execute_command_and_quit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    if not fn.os.path.isfile("/tmp/arcologout.lock"):
        with open("/tmp/arcologout.pid", "w") as f:
            f.write(str(fn.os.getpid()))
            f.close()
        w = TransparentWindow()
        w.show_all()
        Gtk.main()
    else:
        print("arcolinux-logout did not close properly. Remove /tmp/arcologout.lock with sudo.")
