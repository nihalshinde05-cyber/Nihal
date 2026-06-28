import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.utils import get_color_from_hex


def kh(hex_str):
    if hex_str.startswith("#"):
        if len(hex_str) == 7:
            return get_color_from_hex(hex_str + "FF")
        return get_color_from_hex(hex_str)
    return [0.5, 0.5, 0.5, 1]


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


class ChapterTrackerApp(App):
    def build(self):
        self.title = "Chapter Notes Tracker"
        self.load_data()
        self.status_filter = "all"
        self.subject_filter = None

        self.root = BoxLayout(orientation='vertical', padding=20, spacing=15)

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        title_box = BoxLayout(orientation='vertical')
        title_box.add_widget(Label(text="STUDY TRACKER", font_size=12, bold=True,
                                    color=kh("#6366F1"), halign='left',
                                    size_hint_x=None, width=200))
        self.main_title = Label(text="Chapter Notes", font_size=26, bold=True,
                                 color=kh("#1E293B"), halign='left',
                                 size_hint_x=None, width=200)
        title_box.add_widget(self.main_title)
        header.add_widget(title_box)

        self.stats_label = Label(text="0/0\ndone", font_size=14, color=kh("#1E293B"),
                                  bold=True, size_hint_x=None, width=80)
        header.add_widget(self.stats_label)
        self.root.add_widget(header)

        progress_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                                  height=30, spacing=10)
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_x=0.8)
        self.progress_pct = Label(text="0%", font_size=14, color=kh("#64748B"),
                                   bold=True, size_hint_x=0.2)
        progress_box.add_widget(self.progress_bar)
        progress_box.add_widget(self.progress_pct)
        self.root.add_widget(progress_box)

        filter_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                                height=40, spacing=5)
        filter_box.add_widget(Button(text="All",
                                      on_press=lambda x: self.set_status_filter("all"),
                                      background_color=kh("#1E293B")))
        filter_box.add_widget(Button(text="Pending",
                                      on_press=lambda x: self.set_status_filter("pending"),
                                      background_color=kh("#64748B")))
        filter_box.add_widget(Button(text="Done",
                                      on_press=lambda x: self.set_status_filter("done"),
                                      background_color=kh("#64748B")))
        filter_box.add_widget(Button(text="Reset", on_press=self.reset_all,
                                      background_color=kh("#EF4444"), size_hint_x=0.25))
        self.root.add_widget(filter_box)

        add_box = BoxLayout(orientation='vertical', size_hint_y=None, height=130, spacing=5)
        inputs_row = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=40)
        self.title_input = TextInput(hint_text="Chapter title", multiline=False)
        self.subtitle_input = TextInput(hint_text="Subtitle (optional)", multiline=False)
        inputs_row.add_widget(self.title_input)
        inputs_row.add_widget(self.subtitle_input)
        add_box.add_widget(inputs_row)

        meta_row = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=40)
        self.subject_spinner = Spinner(text="Select Subject",
                                        values=[s["name"] for s in self.data["subjects"]])
        self.deadline_input = TextInput(hint_text="YYYY-MM-DD", multiline=False)
        meta_row.add_widget(self.subject_spinner)
        meta_row.add_widget(self.deadline_input)
        add_box.add_widget(meta_row)

        add_btn = Button(text="+ Add Chapter", on_press=self.add_chapter,
                          background_color=kh("#22C55E"), size_hint_y=None, height=35)
        add_box.add_widget(add_btn)
        self.root.add_widget(add_box)

        self.scroll_view = ScrollView()
        self.grid_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        self.scroll_view.add_widget(self.grid_layout)
        self.root.add_widget(self.scroll_view)

        self.refresh_ui()
        return self.root

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
        self.progress_bar.value = pct
        self.progress_pct.text = f"{pct}%"

        for c in chapters:
            if self.status_filter == "pending" and c["done"]:
                continue
            if self.status_filter == "done" and not c["done"]:
                continue

            sub = next((s for s in subjects if s["id"] == c["subject"]), None)
            sub_color = kh(sub["color"]) if sub else kh("#CBD5E1")
            sub_name = sub["name"] if sub else "No Subject"

            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=70,
                             spacing=10, padding=5)

            cb = CheckBox(active=c["done"], size_hint_x=None, width=40)
            cb.bind(active=lambda instance, value, cid=c["id"]:
                    self.toggle_chapter(cid, 'down' if value else 'normal'))
            row.add_widget(cb)

            info_box = BoxLayout(orientation='vertical')
            title_text = f"[b]{c['title']}[/b] ({sub_name})"
            if c["subtitle"]:
                title_text += f"\n[size=12]{c['subtitle']}[/size]"
            if c["deadline"]:
                title_text += f" - [size=12]Due: {c['deadline']}[/size]"

            info_lbl = Label(text=title_text, markup=True, color=kh("#1E293B"),
                              halign='left', valign='middle')
            info_lbl.bind(size=info_lbl.setter('text_size'))
            info_box.add_widget(info_lbl)
            row.add_widget(info_box)

            del_btn = Button(text="X", size_hint_x=None, width=40,
                              background_color=kh("#EF4444"),
                              on_press=lambda x, cid=c["id"]: self.delete_chapter(cid))
            row.add_widget(del_btn)

            self.grid_layout.add_widget(row)


if __name__ == "__main__":
    ChapterTrackerApp().run()
