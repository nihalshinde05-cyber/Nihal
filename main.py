import json
import os
from datetime import datetime
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle, RoundedRectangle


def kh(hex_str):
    if hex_str.startswith("#"):
        if len(hex_str) == 7:
            return get_color_from_hex(hex_str + "FF")
        return get_color_from_hex(hex_str)
    return [0.5, 0.5, 0.5, 1]


BG = "#F1F5F9"
CARD = "#FFFFFF"
TEXT_DARK = "#1E293B"
TEXT_MUTED = "#64748B"
INDIGO = "#6366F1"
INDIGO_LIGHT = "#E0E7FF"
BORDER = "#E2E8F0"
RED = "#EF4444"
GREEN = "#22C55E"

PALETTE = ["#3B82F6", "#8B5CF6", "#EC4899", "#F97316", "#14B8A6", "#EF4444",
           "#EAB308", "#22C55E"]

DEFAULT_DATA = {
    "subjects": [
        {"id": "s1", "name": "Math", "color": "#3B82F6"},
        {"id": "s2", "name": "Science", "color": "#14B8A6"},
        {"id": "s3", "name": "History", "color": "#F97316"},
        {"id": "s4", "name": "English", "color": "#EC4899"},
    ],
    "chapters": [
        {"id": 1, "title": "Chapter 1", "subtitle": "Introduction", "subject": "s1", "deadline": "", "done": False},
        {"id": 2, "title": "Chapter 2", "subtitle": "", "subject": "s1", "deadline": "", "done": False},
        {"id": 3, "title": "Chapter 3", "subtitle": "", "subject": "s2", "deadline": "", "done": False},
        {"id": 4, "title": "Chapter 4", "subtitle": "", "subject": "s3", "deadline": "", "done": False},
        {"id": 5, "title": "Chapter 5", "subtitle": "", "subject": "s4", "deadline": "", "done": False},
        {"id": 6, "title": "Chapter 6", "subtitle": "", "subject": "s2", "deadline": "", "done": False},
    ],
}


class Card(BoxLayout):
    def __init__(self, bg_hex=CARD, radius=16, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*kh(bg_hex))
            self._rect = RoundedRectangle(radius=[radius])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class ColorBar(Widget):
    def __init__(self, color_hex, **kwargs):
        kwargs.setdefault("size_hint_x", None)
        kwargs.setdefault("width", 6)
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*kh(color_hex))
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class ProgressTrack(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pct = 0
        with self.canvas.before:
            Color(*kh(BORDER))
            self._track = RoundedRectangle(radius=[10])
            Color(*kh(INDIGO))
            self._fill = RoundedRectangle(radius=[10])
        self.bind(pos=self._redraw, size=self._redraw)

    def set_pct(self, pct):
        self.pct = max(0, min(100, pct))
        self._redraw()

    def _redraw(self, *args):
        r = self.height / 2 if self.height else 10
        self._track.radius = [r]
        self._track.pos = self.pos
        self._track.size = self.size
        fill_w = self.size[0] * (self.pct / 100)
        self._fill.radius = [r]
        self._fill.pos = self.pos
        self._fill.size = (fill_w, self.size[1])


def flat_button(text, **kwargs):
    kwargs.setdefault("background_normal", "")
    kwargs.setdefault("background_down", "")
    kwargs.setdefault("color", kh("#FFFFFF"))
    return Button(text=text, **kwargs)


class ChapterTrackerApp(App):
    def build(self):
        self.title = "Chapter Notes Tracker"
        Window.clearcolor = kh(BG)
        self.load_data()
        self.status_filter = "all"
        self.subject_filter = None
        self.filter_buttons = {}

        self.root = BoxLayout(orientation='vertical', padding=16, spacing=14)

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=64)
        title_box = BoxLayout(orientation='vertical')
        title_box.add_widget(Label(text="STUDY TRACKER", font_size=12, bold=True,
                                    color=kh(INDIGO), halign='left', valign='bottom',
                                    size_hint_x=None, width=220))
        self.main_title = Label(text="Chapter Notes", font_size=26, bold=True,
                                 color=kh(TEXT_DARK), halign='left', valign='top',
                                 size_hint_x=None, width=220)
        title_box.add_widget(self.main_title)
        header.add_widget(title_box)

        stats_card = Card(bg_hex=INDIGO_LIGHT, radius=14, orientation='vertical',
                           size_hint=(None, None), size=(72, 56), padding=4)
        self.stats_label = Label(text="0/0\ndone", font_size=13, color=kh(INDIGO),
                                  bold=True, halign='center')
        stats_card.add_widget(self.stats_label)
        header.add_widget(stats_card)
        self.root.add_widget(header)

        progress_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                                  height=22, spacing=10)
        self.progress_bar = ProgressTrack(size_hint_x=0.85)
        self.progress_pct = Label(text="0%", font_size=14, color=kh(TEXT_MUTED),
                                   bold=True, size_hint_x=0.15)
        progress_box.add_widget(self.progress_bar)
        progress_box.add_widget(self.progress_pct)
        self.root.add_widget(progress_box)

        filter_card = Card(bg_hex=CARD, radius=14, orientation='horizontal',
                            size_hint_y=None, height=44, spacing=6, padding=4)
        for key, label in (("all", "All"), ("pending", "Pending"), ("done", "Done")):
            btn = flat_button(label, on_press=lambda x, k=key: self.set_status_filter(k))
            self.filter_buttons[key] = btn
            filter_card.add_widget(btn)
        reset_btn = flat_button("Reset", on_press=self.reset_all,
                                 background_color=kh(RED), size_hint_x=0.5)
        filter_card.add_widget(reset_btn)
        self.root.add_widget(filter_card)
        self._update_filter_styles()

        add_card = Card(bg_hex=CARD, radius=16, orientation='vertical',
                         size_hint_y=None, height=160, spacing=8, padding=12)
        inputs_row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=42)
        self.title_input = TextInput(hint_text="Chapter title", multiline=False,
                                      background_color=kh("#F8FAFC"),
                                      foreground_color=kh(TEXT_DARK),
                                      hint_text_color=kh(TEXT_MUTED), padding=[10, 10, 10, 10])
        self.subtitle_input = TextInput(hint_text="Subtitle (optional)", multiline=False,
                                         background_color=kh("#F8FAFC"),
                                         foreground_color=kh(TEXT_DARK),
                                         hint_text_color=kh(TEXT_MUTED), padding=[10, 10, 10, 10])
        inputs_row.add_widget(self.title_input)
        inputs_row.add_widget(self.subtitle_input)
        add_card.add_widget(inputs_row)

        meta_row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=42)
        self.subject_spinner = Spinner(text="Select Subject",
                                        values=[s["name"] for s in self.data["subjects"]],
                                        background_normal='', background_down='',
                                        background_color=kh("#F8FAFC"), color=kh(TEXT_DARK))
        self.deadline_input = TextInput(hint_text="YYYY-MM-DD", multiline=False,
                                         background_color=kh("#F8FAFC"),
                                         foreground_color=kh(TEXT_DARK),
                                         hint_text_color=kh(TEXT_MUTED), padding=[10, 10, 10, 10])
        meta_row.add_widget(self.subject_spinner)
        meta_row.add_widget(self.deadline_input)
        add_card.add_widget(meta_row)

        add_btn = flat_button("+ Add Chapter", on_press=self.add_chapter,
                               background_color=kh(GREEN), size_hint_y=None, height=38)
        add_card.add_widget(add_btn)
        self.root.add_widget(add_card)

        self.scroll_view = ScrollView()
        self.grid_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        self.scroll_view.add_widget(self.grid_layout)
        self.root.add_widget(self.scroll_view)

        self.refresh_ui()
        return self.root

    def _update_filter_styles(self):
        for key, btn in self.filter_buttons.items():
            if key == self.status_filter:
                btn.background_color = kh(INDIGO)
                btn.color = kh("#FFFFFF")
            else:
                btn.background_color = kh("#F1F5F9")
                btn.color = kh(TEXT_DARK)

    def load_data(self):
        self.storage_file = "chapter_tracker_data.json"
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = DEFAULT_DATA
        else:
            self.data = DEFAULT_DATA

    def save_data(self):
        with open(self.storage_file, "w") as f:
            json.dump(self.data, f)

    def set_status_filter(self, status):
        self.status_filter = status
        self._update_filter_styles()
        self.refresh_ui()

    def reset_all(self, instance):
        for c in self.data["chapters"]:
            c["done"] = False
        self.save_data()
        self.refresh_ui()

    def add_chapter(self, instance):
        title = self.title_input.text.strip()
        if not title:
            return
        subtitle = self.subtitle_input.text.strip()
        deadline = self.deadline_input.text.strip()

        selected_sub_name = self.subject_spinner.text
        sub_id = ""
        for s in self.data["subjects"]:
            if s["name"] == selected_sub_name:
                sub_id = s["id"]
                break

        new_item = {
            "id": int(datetime.now().timestamp() * 1000),
            "title": title,
            "subtitle": subtitle,
            "subject": sub_id,
            "deadline": deadline,
            "done": False
        }
        self.data["chapters"].append(new_item)
        self.save_data()

        self.title_input.text = ""
        self.subtitle_input.text = ""
        self.deadline_input.text = ""
        self.subject_spinner.text = "Select Subject"
        self.refresh_ui()

    def toggle_chapter(self, chapter_id, state):
        for c in self.data["chapters"]:
            if c["id"] == chapter_id:
                c["done"] = (state == 'down')
                break
        self.save_data()
        self.refresh_ui()

    def delete_chapter(self, chapter_id):
        self.data["chapters"] = [c for c in self.data["chapters"] if c["id"] != chapter_id]
        self.save_data()
        self.refresh_ui()

    def refresh_ui(self):
        self.grid_layout.clear_widgets()
        chapters = self.data["chapters"]
        subjects = self.data["subjects"]

        done_count = len([c for c in chapters if c["done"]])
        total_count = len(chapters)
        pct = round((done_count / total_count) * 100) if total_count > 0 else 0

        self.stats_label.text = f"{done_count}/{total_count}\ndone"
        self.progress_bar.set_pct(pct)
        self.progress_pct.text = f"{pct}%"

        for c in chapters:
            if self.status_filter == "pending" and c["done"]:
                continue
            if self.status_filter == "done" and not c["done"]:
                continue

            sub = next((s for s in subjects if s["id"] == c["subject"]), None)
            sub_color = sub["color"] if sub else "#CBD5E1"
            sub_name = sub["name"] if sub else "No Subject"

            row = Card(bg_hex=CARD, radius=14, orientation='horizontal',
                       size_hint_y=None, height=72, spacing=10, padding=[0, 8, 8, 8])

            row.add_widget(ColorBar(sub_color))

            cb = CheckBox(active=c["done"], size_hint_x=None, width=40)
            cb.bind(active=lambda instance, value, cid=c["id"]:
                    self.toggle_chapter(cid, 'down' if value else 'normal'))
            row.add_widget(cb)

            info_box = BoxLayout(orientation='vertical')
            title_text = f"[b]{c['title']}[/b] ({sub_name})"
            if c["subtitle"]:
                title_text += f"\n[size=12][color=64748B]{c['subtitle']}[/color][/size]"
            if c["deadline"]:
                title_text += f" - [size=12][color=64748B]Due: {c['deadline']}[/color][/size]"

            info_lbl = Label(text=title_text, markup=True, color=kh(TEXT_DARK),
                              halign='left', valign='middle')
            info_lbl.bind(size=info_lbl.setter('text_size'))
            info_box.add_widget(info_lbl)
            row.add_widget(info_box)

            del_btn = flat_button("X", size_hint_x=None, width=40,
                                   background_color=kh(RED),
                                   on_press=lambda x, cid=c["id"]: self.delete_chapter(cid))
            row.add_widget(del_btn)

            self.grid_layout.add_widget(row)


if __name__ == "__main__":
    ChapterTrackerApp().run()
