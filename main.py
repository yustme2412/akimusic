"""
AkiMusic - Spotify Downloader for Android
Main application entry point with Kivy UI
"""

import os
import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image, AsyncImage
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty

import library
import downloader
import player
import json

# ─── COLORES ─────────────────────────────────────────────
BG_BLACK      = (0.05, 0.05, 0.05, 1)
BG_CARD       = (0.10, 0.10, 0.10, 1)
BG_INPUT      = (0.15, 0.15, 0.15, 1)
WHITE         = (1, 1, 1, 1)
GREY_LIGHT    = (0.75, 0.75, 0.75, 1)
GREY_MID      = (0.45, 0.45, 0.45, 1)
GREY_DARK     = (0.20, 0.20, 0.20, 1)
ACCENT        = (0.9, 0.9, 0.9, 1)

Window.clearcolor = BG_BLACK

# ─── KV LANG (estilos globales) ───────────────────────────
KV = """
<RoundButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.9, 0.9, 0.9, 1) if self.state == 'normal' else (0.6, 0.6, 0.6, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(25)]

<GhostButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    color: 0.9, 0.9, 0.9, 1
    canvas.before:
        Color:
            rgba: (0.18, 0.18, 0.18, 1) if self.state == 'normal' else (0.25, 0.25, 0.25, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(25)]
        Color:
            rgba: 0.35, 0.35, 0.35, 1
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, dp(25)]
            width: 1

<SongCard@RelativeLayout>:
    size_hint_y: None
    height: dp(80)
    canvas.before:
        Color:
            rgba: 0.10, 0.10, 0.10, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
"""

Builder.load_string(KV)


# ─── SPLASH SCREEN ────────────────────────────────────────
class SplashScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.go_home, 2.0)

    def go_home(self, dt):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'home'

    def build_ui(self):
        layout = FloatLayout()
        with layout.canvas.before:
            Color(*BG_BLACK)
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)

        # Logo texto
        logo = Label(
            text="AkiMusic",
            font_size=sp(48),
            bold=True,
            color=WHITE,
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
            size_hint=(None, None),
            size=(dp(300), dp(80))
        )
        subtitle = Label(
            text="Tu música. Sin límites.",
            font_size=sp(14),
            color=GREY_LIGHT,
            pos_hint={'center_x': 0.5, 'center_y': 0.44},
            size_hint=(None, None),
            size=(dp(300), dp(30))
        )
        layout.add_widget(logo)
        layout.add_widget(subtitle)
        self.add_widget(layout)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


# ─── HOME / DOWNLOAD SCREEN ───────────────────────────────
class HomeScreen(Screen):
    status_text = StringProperty("Listo para descargar")
    progress_val = NumericProperty(0)
    is_downloading = BooleanProperty(False)

    def on_kv_post(self, base_widget):
        pass

    def build_ui(self):
        root = BoxLayout(orientation='vertical', spacing=0)

        # Header
        header = self._make_header()
        root.add_widget(header)

        # Scroll content
        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=[dp(20), dp(10), dp(20), dp(20)],
            spacing=dp(16)
        )
        content.bind(minimum_height=content.setter('height'))

        # Input section
        input_card = self._make_input_card()
        content.add_widget(input_card)

        # Progress section
        self.progress_section = self._make_progress_section()
        content.add_widget(self.progress_section)

        # Library section header
        lib_header = BoxLayout(size_hint_y=None, height=dp(44), padding=[dp(4), 0])
        lib_title = Label(text="Biblioteca", font_size=sp(18), bold=True, color=WHITE,
                          size_hint_x=None, width=dp(120), halign='left', valign='middle')
        lib_title.bind(size=lib_title.setter('text_size'))
        lib_btn = Button(
            text="Ver todo →", font_size=sp(12), color=GREY_LIGHT,
            background_color=(0,0,0,0), background_normal='',
            size_hint_x=None, width=dp(80)
        )
        lib_btn.bind(on_press=lambda x: self.go_library())
        lib_header.add_widget(lib_title)
        lib_header.add_widget(Label())  # spacer
        lib_header.add_widget(lib_btn)
        content.add_widget(lib_header)

        # Recent songs grid
        self.songs_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(8)
        )
        self.songs_container.bind(minimum_height=self.songs_container.setter('height'))
        content.add_widget(self.songs_container)

        scroll.add_widget(content)
        root.add_widget(scroll)

        # Bottom nav
        nav = self._make_bottom_nav()
        root.add_widget(nav)

        self.add_widget(root)
        self.load_recent_songs()

    def _make_header(self):
        header = BoxLayout(
            size_hint_y=None, height=dp(64),
            padding=[dp(20), dp(8), dp(20), dp(8)]
        )
        with header.canvas.before:
            Color(0.07, 0.07, 0.07, 1)
            self._hdr_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(self._hdr_rect, 'pos', v),
                    size=lambda i, v: setattr(self._hdr_rect, 'size', v))

        title = Label(
            text="AkiMusic", font_size=sp(22), bold=True,
            color=WHITE, halign='left', valign='middle'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        return header

    def _make_input_card(self):
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=None, height=dp(180),
            padding=[dp(16), dp(16)], spacing=dp(12)
        )
        with card.canvas.before:
            Color(*BG_CARD)
            self._card_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(16)])
        card.bind(pos=lambda i, v: setattr(self._card_rect, 'pos', v),
                  size=lambda i, v: setattr(self._card_rect, 'size', v))

        hint = Label(
            text="Pega aquí un enlace de música o playlist",
            font_size=sp(13), color=GREY_MID,
            size_hint_y=None, height=dp(24), halign='left', valign='middle'
        )
        hint.bind(size=hint.setter('text_size'))

        self.url_input = TextInput(
            hint_text="Spotify, YouTube, SoundCloud o enlace de música...",
            multiline=False,
            size_hint_y=None, height=dp(52),
            background_color=BG_INPUT,
            foreground_color=WHITE,
            hint_text_color=GREY_MID,
            cursor_color=WHITE,
            font_size=sp(13),
            padding=[dp(14), dp(14)],
        )

        btn_row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))
        
        clear_btn = Button(
            text="Limpiar",
            background_color=(0.18, 0.18, 0.18, 1),
            background_normal='',
            color=GREY_LIGHT,
            font_size=sp(13),
            size_hint_x=0.35
        )
        clear_btn.bind(on_press=lambda x: setattr(self.url_input, 'text', ''))

        self.download_btn = Button(
            text="⬇  Descargar",
            background_color=(0.9, 0.9, 0.9, 1),
            background_normal='',
            color=(0.05, 0.05, 0.05, 1),
            bold=True,
            font_size=sp(14),
            size_hint_x=0.65
        )
        self.download_btn.bind(on_press=self.start_download)

        btn_row.add_widget(clear_btn)
        btn_row.add_widget(self.download_btn)

        card.add_widget(hint)
        card.add_widget(self.url_input)
        card.add_widget(btn_row)
        return card

    def _make_progress_section(self):
        section = BoxLayout(
            orientation='vertical',
            size_hint_y=None, height=dp(90),
            padding=[dp(16), dp(10)], spacing=dp(8)
        )
        with section.canvas.before:
            Color(*BG_CARD)
            self._prog_rect = RoundedRectangle(pos=section.pos, size=section.size, radius=[dp(16)])
        section.bind(pos=lambda i, v: setattr(self._prog_rect, 'pos', v),
                     size=lambda i, v: setattr(self._prog_rect, 'size', v))

        self.status_label = Label(
            text=self.status_text,
            font_size=sp(13), color=GREY_LIGHT,
            size_hint_y=None, height=dp(24),
            halign='left', valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))

        self.progress_bar = ProgressBar(
            max=100, value=0,
            size_hint_y=None, height=dp(8)
        )
        # Estilo de la barra
        with self.progress_bar.canvas.before:
            Color(*GREY_DARK)
            self._pb_bg = RoundedRectangle(
                pos=self.progress_bar.pos,
                size=self.progress_bar.size,
                radius=[dp(4)]
            )
        self.progress_bar.bind(
            pos=lambda i, v: setattr(self._pb_bg, 'pos', v),
            size=lambda i, v: setattr(self._pb_bg, 'size', v)
        )

        section.add_widget(self.status_label)
        section.add_widget(self.progress_bar)
        return section

    def _make_bottom_nav(self):
        nav = BoxLayout(size_hint_y=None, height=dp(64), padding=[dp(8), dp(8)])
        with nav.canvas.before:
            Color(0.07, 0.07, 0.07, 1)
            self._nav_rect = Rectangle(pos=nav.pos, size=nav.size)
        nav.bind(pos=lambda i, v: setattr(self._nav_rect, 'pos', v),
                 size=lambda i, v: setattr(self._nav_rect, 'size', v))

        home_btn = Button(
            text="⬇\nInicio", font_size=sp(10), color=WHITE,
            background_color=(0,0,0,0), background_normal='',
            halign='center'
        )
        lib_btn = Button(
            text="♫\nBiblioteca", font_size=sp(10), color=GREY_MID,
            background_color=(0,0,0,0), background_normal='',
            halign='center'
        )
        lib_btn.bind(on_press=lambda x: self.go_library())
        set_btn = Button(
            text="⚙\nAjustes", font_size=sp(10), color=GREY_MID,
            background_color=(0,0,0,0), background_normal='',
            halign='center'
        )
        set_btn.bind(on_press=lambda x: self.go_settings())

        nav.add_widget(home_btn)
        nav.add_widget(lib_btn)
        nav.add_widget(set_btn)
        return nav

    def start_download(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self._show_popup("Error", "Por favor pega un enlace de canción o playlist primero.")
            return
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("spotify:")):
            self._show_popup("Enlace inválido", "Por favor ingresa un enlace web válido (Spotify, YouTube, etc.).")
            return

        self.is_downloading = True
        self.download_btn.text = "Descargando..."
        self.download_btn.background_color = (0.4, 0.4, 0.4, 1)
        self.download_btn.disabled = True
        self.update_status("Iniciando descarga...", 0)

        thread = threading.Thread(
            target=self._download_worker,
            args=(url,),
            daemon=True
        )
        thread.start()

    def _download_worker(self, url):
        def progress_cb(status, percent, song_name=""):
            Clock.schedule_once(lambda dt: self.update_status(
                f"{status}: {song_name}" if song_name else status, percent
            ))

        def done_cb(success, message):
            Clock.schedule_once(lambda dt: self._on_download_done(success, message))

        downloader.download(url, progress_cb, done_cb)

    def _on_download_done(self, success, message):
        self.is_downloading = False
        self.download_btn.text = "⬇  Descargar"
        self.download_btn.background_color = (0.9, 0.9, 0.9, 1)
        self.download_btn.disabled = False

        if success:
            self.update_status("✓ Descarga completada", 100)
            self.url_input.text = ""
            self.load_recent_songs()
            self._show_popup("¡Listo!", message)
        else:
            self.update_status("✗ Error en la descarga", 0)
            self._show_popup("Error", message)

    def update_status(self, text, progress):
        self.status_label.text = text
        self.progress_bar.value = progress

    def load_recent_songs(self):
        self.songs_container.clear_widgets()
        songs = library.get_songs(limit=5)
        if not songs:
            empty = Label(
                text="No hay canciones aún. ¡Descarga la primera!",
                font_size=sp(13), color=GREY_MID,
                size_hint_y=None, height=dp(50)
            )
            self.songs_container.add_widget(empty)
        for s in songs:
            card = self._make_song_card(s)
            self.songs_container.add_widget(card)

    def _make_song_card(self, song_info):
        card = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(72),
            padding=[dp(12), dp(8)], spacing=dp(12)
        )
        with card.canvas.before:
            Color(*BG_CARD)
            rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                  size=lambda i, v: setattr(rect, 'size', v))

        # Thumbnail
        thumb_container = BoxLayout(size_hint=(None, None), size=(dp(56), dp(56)))
        with thumb_container.canvas.before:
            Color(*GREY_DARK)
            thumb_rect = RoundedRectangle(pos=thumb_container.pos,
                                          size=thumb_container.size, radius=[dp(8)])
        thumb_container.bind(pos=lambda i, v: setattr(thumb_rect, 'pos', v),
                              size=lambda i, v: setattr(thumb_rect, 'size', v))

        if song_info.get('cover'):
            img = AsyncImage(source=song_info['cover'], allow_stretch=True, keep_ratio=True)
            thumb_container.add_widget(img)
        else:
            note = Label(text="♫", font_size=sp(24), color=GREY_MID)
            thumb_container.add_widget(note)

        # Info
        info = BoxLayout(orientation='vertical', spacing=dp(2))
        title_label = Label(
            text=song_info.get('title', 'Sin título'),
            font_size=sp(14), bold=True, color=WHITE,
            halign='left', valign='middle', size_hint_y=None, height=dp(22)
        )
        title_label.bind(size=title_label.setter('text_size'))
        artist_label = Label(
            text=song_info.get('artist', 'Artista desconocido'),
            font_size=sp(12), color=GREY_MID,
            halign='left', valign='middle', size_hint_y=None, height=dp(18)
        )
        artist_label.bind(size=artist_label.setter('text_size'))
        info.add_widget(title_label)
        info.add_widget(artist_label)

        # Play button
        play_btn = Button(
            text="▶", font_size=sp(20), color=WHITE,
            background_color=(0,0,0,0), background_normal='',
            size_hint=(None, None), size=(dp(40), dp(40))
        )
        play_btn.bind(on_press=lambda x: self.play_song(song_info))

        card.add_widget(thumb_container)
        card.add_widget(info)
        card.add_widget(play_btn)
        return card

    def play_song(self, song_info):
        path = song_info.get('path', '')
        if os.path.exists(path):
            player.play(path)

    def go_library(self):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'library'

    def go_settings(self):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'settings'

    def _show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(16))
        msg = Label(text=message, color=WHITE, font_size=sp(14),
                    halign='center', valign='middle')
        msg.bind(size=msg.setter('text_size'))
        close_btn = Button(
            text="Cerrar", size_hint_y=None, height=dp(44),
            background_color=(0.9, 0.9, 0.9, 1), background_normal='',
            color=(0.05, 0.05, 0.05, 1), bold=True
        )
        content.add_widget(msg)
        content.add_widget(close_btn)
        popup = Popup(
            title=title, content=content,
            size_hint=(0.85, 0.4),
            background='', background_color=(0.1, 0.1, 0.1, 0.97),
            title_color=WHITE, title_size=sp(16),
            separator_color=GREY_DARK
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


# ─── LIBRARY SCREEN ───────────────────────────────────────
class LibraryScreen(Screen):
    def build_ui(self):
        root = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(
            size_hint_y=None, height=dp(64),
            padding=[dp(16), dp(8), dp(16), dp(8)]
        )
        with header.canvas.before:
            Color(0.07, 0.07, 0.07, 1)
            hdr_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(hdr_rect, 'pos', v),
                    size=lambda i, v: setattr(hdr_rect, 'size', v))

        back_btn = Button(
            text="← Atrás", font_size=sp(14), color=WHITE,
            background_color=(0,0,0,0), background_normal='',
            size_hint_x=None, width=dp(80)
        )
        back_btn.bind(on_press=self.go_back)
        title = Label(text="Biblioteca", font_size=sp(20), bold=True, color=WHITE)
        header.add_widget(back_btn)
        header.add_widget(title)
        root.add_widget(header)

        # Songs list
        scroll = ScrollView(size_hint=(1, 1))
        self.songs_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=[dp(16), dp(12)], spacing=dp(10)
        )
        self.songs_layout.bind(minimum_height=self.songs_layout.setter('height'))
        scroll.add_widget(self.songs_layout)
        root.add_widget(scroll)

        # Player bar at bottom
        self.player_bar = self._make_player_bar()
        root.add_widget(self.player_bar)

        self.add_widget(root)

    def on_enter(self):
        self.load_songs()
        Clock.schedule_interval(self._update_player, 0.5)

    def on_leave(self):
        Clock.unschedule(self._update_player)

    def load_songs(self):
        self.songs_layout.clear_widgets()
        songs = library.get_songs()
        if not songs:
            empty = Label(
                text="No hay canciones descargadas aún.\nVuelve a inicio y descarga algo!",
                font_size=sp(14), color=GREY_MID,
                size_hint_y=None, height=dp(100),
                halign='center', valign='middle'
            )
            empty.bind(size=empty.setter('text_size'))
            self.songs_layout.add_widget(empty)
            return
        for s in songs:
            card = self._make_library_card(s)
            self.songs_layout.add_widget(card)

    def _make_library_card(self, song_info):
        card = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(80),
            padding=[dp(14), dp(10)], spacing=dp(14)
        )
        with card.canvas.before:
            Color(*BG_CARD)
            rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(14)])
        card.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                  size=lambda i, v: setattr(rect, 'size', v))

        # Art
        art = BoxLayout(size_hint=(None, None), size=(dp(60), dp(60)))
        with art.canvas.before:
            Color(*GREY_DARK)
            art_rect = RoundedRectangle(pos=art.pos, size=art.size, radius=[dp(10)])
        art.bind(pos=lambda i, v: setattr(art_rect, 'pos', v),
                 size=lambda i, v: setattr(art_rect, 'size', v))
        if song_info.get('cover'):
            art.add_widget(AsyncImage(source=song_info['cover'],
                                      allow_stretch=True, keep_ratio=True))
        else:
            art.add_widget(Label(text="♫", font_size=sp(26), color=GREY_MID))

        # Text
        text_col = BoxLayout(orientation='vertical', spacing=dp(4))
        ttl = Label(text=song_info.get('title', '?'), font_size=sp(14),
                    bold=True, color=WHITE, halign='left',
                    size_hint_y=None, height=dp(22))
        ttl.bind(size=ttl.setter('text_size'))
        art_lbl = Label(
            text=f"{song_info.get('artist', '?')} · {song_info.get('album', '')}",
            font_size=sp(12), color=GREY_MID, halign='left',
            size_hint_y=None, height=dp(18)
        )
        art_lbl.bind(size=art_lbl.setter('text_size'))
        text_col.add_widget(ttl)
        text_col.add_widget(art_lbl)

        # Actions
        actions = BoxLayout(size_hint=(None, 1), width=dp(80), spacing=dp(4))
        play_btn = Button(
            text="▶", font_size=sp(22), color=WHITE,
            background_color=(0,0,0,0), background_normal='',
            size_hint_x=None, width=dp(40)
        )
        play_btn.bind(on_press=lambda x: self._play(song_info))
        del_btn = Button(
            text="✕", font_size=sp(16), color=GREY_MID,
            background_color=(0,0,0,0), background_normal='',
            size_hint_x=None, width=dp(40)
        )
        del_btn.bind(on_press=lambda x: self._delete(song_info))
        actions.add_widget(play_btn)
        actions.add_widget(del_btn)

        card.add_widget(art)
        card.add_widget(text_col)
        card.add_widget(actions)
        return card

    def _make_player_bar(self):
        bar = BoxLayout(
            size_hint_y=None, height=dp(72),
            padding=[dp(16), dp(10)], spacing=dp(12)
        )
        with bar.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            bar_rect = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda i, v: setattr(bar_rect, 'pos', v),
                 size=lambda i, v: setattr(bar_rect, 'size', v))

        self.now_playing_lbl = Label(
            text="Sin reproducir", font_size=sp(13),
            color=GREY_LIGHT, halign='left', valign='middle'
        )
        self.now_playing_lbl.bind(size=self.now_playing_lbl.setter('text_size'))

        ctrl_box = BoxLayout(size_hint_x=None, width=dp(130), spacing=dp(4))
        prev_btn = Button(text="⏮", font_size=sp(20), color=WHITE,
                          background_color=(0,0,0,0), background_normal='')
        prev_btn.bind(on_press=lambda x: player.prev())
        self.play_pause_btn = Button(text="⏸", font_size=sp(20), color=WHITE,
                                     background_color=(0,0,0,0), background_normal='')
        self.play_pause_btn.bind(on_press=self._toggle_pause)
        next_btn = Button(text="⏭", font_size=sp(20), color=WHITE,
                          background_color=(0,0,0,0), background_normal='')
        next_btn.bind(on_press=lambda x: player.next_song())
        ctrl_box.add_widget(prev_btn)
        ctrl_box.add_widget(self.play_pause_btn)
        ctrl_box.add_widget(next_btn)

        bar.add_widget(self.now_playing_lbl)
        bar.add_widget(ctrl_box)
        return bar

    def _toggle_pause(self, instance):
        if player.is_playing():
            player.pause()
            self.play_pause_btn.text = "▶"
        else:
            player.resume()
            self.play_pause_btn.text = "⏸"

    def _update_player(self, dt):
        info = player.current_info()
        if info:
            self.now_playing_lbl.text = f"♫  {info.get('title', '')} · {info.get('artist', '')}"
        else:
            self.now_playing_lbl.text = "Sin reproducir"

    def _play(self, song_info):
        path = song_info.get('path', '')
        if os.path.exists(path):
            player.play(path)
            self.play_pause_btn.text = "⏸"

    def _delete(self, song_info):
        library.delete_song(song_info.get('path', ''))
        self.load_songs()

    def go_back(self, instance=None):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


# ─── SETTINGS SCREEN ─────────────────────────────────────
class SettingsScreen(Screen):
    def build_ui(self):
        root = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(
            size_hint_y=None, height=dp(64),
            padding=[dp(16), dp(8), dp(16), dp(8)]
        )
        with header.canvas.before:
            Color(0.07, 0.07, 0.07, 1)
            hdr_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(hdr_rect, 'pos', v),
                    size=lambda i, v: setattr(hdr_rect, 'size', v))
        title = Label(text="Ajustes", font_size=sp(20), bold=True, color=WHITE)
        header.add_widget(title)
        root.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=[dp(20), dp(20)], spacing=dp(16)
        )
        content.bind(minimum_height=content.setter('height'))

        # Info card
        info_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None, height=dp(120),
            padding=[dp(16), dp(14)], spacing=dp(6)
        )
        with info_card.canvas.before:
            Color(*BG_CARD)
            ic_rect = RoundedRectangle(pos=info_card.pos, size=info_card.size, radius=[dp(14)])
        info_card.bind(pos=lambda i, v: setattr(ic_rect, 'pos', v),
                       size=lambda i, v: setattr(ic_rect, 'size', v))
        lbl1 = Label(
            text="AkiMusic - Configuración",
            font_size=sp(15), bold=True, color=WHITE,
            size_hint_y=None, height=dp(26), halign='left', valign='middle'
        )
        lbl1.bind(size=lbl1.setter('text_size'))
        lbl2 = Label(
            text="¡AkiMusic ahora funciona 100% libre sin keys!\nOpcional: puedes ingresar API keys personales como respaldo.",
            font_size=sp(12), color=GREY_MID,
            size_hint_y=None, height=dp(48), halign='left', valign='middle'
        )
        lbl2.bind(size=lbl2.setter('text_size'))
        info_card.add_widget(lbl1)
        info_card.add_widget(lbl2)
        content.add_widget(info_card)

        # Client ID
        lbl_id = Label(
            text="Client ID", font_size=sp(13), color=GREY_LIGHT,
            size_hint_y=None, height=dp(24), halign='left', valign='middle'
        )
        lbl_id.bind(size=lbl_id.setter('text_size'))
        self.client_id_input = TextInput(
            hint_text="Pega tu Spotify Client ID aqui",
            multiline=False, size_hint_y=None, height=dp(52),
            background_color=BG_INPUT, foreground_color=WHITE,
            hint_text_color=GREY_MID, cursor_color=WHITE,
            font_size=sp(13), padding=[dp(14), dp(14)]
        )
        content.add_widget(lbl_id)
        content.add_widget(self.client_id_input)

        # Client Secret
        lbl_sec = Label(
            text="Client Secret", font_size=sp(13), color=GREY_LIGHT,
            size_hint_y=None, height=dp(24), halign='left', valign='middle'
        )
        lbl_sec.bind(size=lbl_sec.setter('text_size'))
        self.client_secret_input = TextInput(
            hint_text="Pega tu Spotify Client Secret aqui",
            multiline=False, size_hint_y=None, height=dp(52),
            background_color=BG_INPUT, foreground_color=WHITE,
            hint_text_color=GREY_MID, cursor_color=WHITE,
            font_size=sp(13), padding=[dp(14), dp(14)],
            password=True
        )
        content.add_widget(lbl_sec)
        content.add_widget(self.client_secret_input)

        # Save button
        save_btn = Button(
            text="Guardar y continuar",
            background_color=(0.9, 0.9, 0.9, 1), background_normal='',
            color=(0.05, 0.05, 0.05, 1), bold=True,
            font_size=sp(15), size_hint_y=None, height=dp(54)
        )
        save_btn.bind(on_press=self.save_credentials)
        content.add_widget(save_btn)

        # Link hint
        hint = Label(
            text="developer.spotify.com  →  Log in  →  Create app\n"
                 "Redirect URI: http://127.0.0.1:8888/callback",
            font_size=sp(11), color=GREY_MID,
            size_hint_y=None, height=dp(50),
            halign='center', valign='middle'
        )
        hint.bind(size=hint.setter('text_size'))
        content.add_widget(hint)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)
        self._load_existing()

    def on_enter(self):
        self._load_existing()

    def _load_existing(self):
        cfg = downloader.load_config()
        self.client_id_input.text = cfg.get('spotify_client_id', '')
        self.client_secret_input.text = cfg.get('spotify_client_secret', '')

    def save_credentials(self, instance):
        cid = self.client_id_input.text.strip()
        csec = self.client_secret_input.text.strip()
        if cid and csec:
            downloader.save_config({'spotify_client_id': cid, 'spotify_client_secret': csec})
            self._popup("Guardado", "Credenciales opcionales guardadas.")
        else:
            self._popup("Modo Automático", "AkiMusic funciona automáticamente sin keys.")
        Clock.schedule_once(lambda dt: self._go_home(), 1.0)

    def _go_home(self):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'home'

    def _popup(self, title, msg):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        lbl = Label(text=msg, color=WHITE, font_size=sp(14), halign='center', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        btn = Button(
            text="OK", size_hint_y=None, height=dp(44),
            background_color=(0.9, 0.9, 0.9, 1), background_normal='',
            color=(0.05, 0.05, 0.05, 1), bold=True
        )
        content.add_widget(lbl)
        content.add_widget(btn)
        p = Popup(
            title=title, content=content,
            size_hint=(0.82, 0.38),
            background='', background_color=(0.1, 0.1, 0.1, 0.97),
            title_color=WHITE, title_size=sp(15),
            separator_color=GREY_DARK
        )
        btn.bind(on_press=p.dismiss)
        p.open()


# ─── APP PRINCIPAL ────────────────────────────────────────
class AkiMusicApp(App):
    def build(self):
        self.title = "AkiMusic"
        sm = ScreenManager()

        splash = SplashScreen(name='splash')
        splash.build_ui()
        sm.add_widget(splash)

        settings_screen = SettingsScreen(name='settings')
        settings_screen.build_ui()
        sm.add_widget(settings_screen)

        home = HomeScreen(name='home')
        home.build_ui()
        sm.add_widget(home)

        library_screen = LibraryScreen(name='library')
        library_screen.build_ui()
        sm.add_widget(library_screen)

        sm.current = 'splash'
        return sm


if __name__ == '__main__':
    AkiMusicApp().run()
