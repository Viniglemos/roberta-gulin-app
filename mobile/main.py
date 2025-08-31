"""
Kivy front‑end for the Roberta Gulin mobile app.

This module defines the graphical user interface and client‑side logic
for interacting with the backend API. The app uses a `ScreenManager` to
navigate between different views: a home screen, a gallery of images,
a calendar view, a notifications interface, and a payment page. Each
screen issues HTTP requests to the Flask API running on the backend
EC2 instance (or locally during development).

To run this application locally, install Kivy and its dependencies
(`pip install kivy requests`) and execute `python main.py`. You may
need to set the environment variable `API_BASE_URL` to point to the
backend server (defaults to `http://localhost:5000`).

Note: This file contains only a skeleton implementation. Additional
features and polish should be added as you iterate on the design.
"""

import os
import json
from typing import List, Dict, Any

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.network.urlrequest import UrlRequest


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000/api")


class HomeScreen(Screen):
    """Main menu screen providing navigation to other sections."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(Label(text="Roberta Gulin Photography", font_size=24, size_hint=(1, 0.2)))

        buttons = [
            ("Gallery", "gallery"),
            ("Calendar", "calendar"),
            ("Payments", "payments"),
            ("Notifications", "notifications"),
            ("About", "about"),
        ]
        for text, screen_name in buttons:
            btn = Button(text=text, size_hint=(1, 0.15))
            btn.bind(on_release=lambda instance, sn=screen_name: self.go_to(sn))
            layout.add_widget(btn)
        self.add_widget(layout)

    def go_to(self, screen_name: str) -> None:
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen_name


class GalleryScreen(Screen):
    """Display images fetched from the backend's gallery endpoint."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        header = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        back_btn = Button(text="< Back", size_hint=(0.2, 1))
        back_btn.bind(on_release=lambda instance: self.go_home())
        header.add_widget(back_btn)
        header.add_widget(Label(text="Gallery", font_size=22))
        self.layout.add_widget(header)

        # Scrollable grid of images
        self.scroll = ScrollView(size_hint=(1, 0.9))
        self.grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def on_pre_enter(self) -> None:
        """Called before the screen is displayed. Trigger loading of images."""
        self.load_images()

    def go_home(self) -> None:
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"

    def load_images(self) -> None:
        """Fetch gallery images from the backend and populate the grid."""
        self.grid.clear_widgets()

        def on_success(req: UrlRequest, result: Any) -> None:
            if not isinstance(result, list):
                return
            for item in result:
                url = item.get("url")
                if url:
                    img = AsyncImage(source=url, size_hint=(1, None), height=200)
                    self.grid.add_widget(img)

        def on_error(req: UrlRequest, error: Any) -> None:
            print(f"Failed to load images: {error}")

        UrlRequest(f"{API_BASE_URL}/gallery", on_success=on_success, on_error=on_error)


class CalendarScreen(Screen):
    """Display upcoming events from Notion."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical")
        header = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        back_btn = Button(text="< Back", size_hint=(0.2, 1))
        back_btn.bind(on_release=lambda instance: self.go_home())
        header.add_widget(back_btn)
        header.add_widget(Label(text="Calendar", font_size=22))
        layout.add_widget(header)
        self.events_box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        scroll = ScrollView()
        scroll.add_widget(self.events_box)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def on_pre_enter(self) -> None:
        self.load_events()

    def go_home(self) -> None:
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"

    def load_events(self) -> None:
        self.events_box.clear_widgets()

        def on_success(req: UrlRequest, result: Any) -> None:
            if not isinstance(result, list):
                return
            for event in result:
                title = event.get("title", "(Untitled)")
                start = event.get("start")
                end = event.get("end")
                text = f"{title}\nStart: {start or 'N/A'}\nEnd: {end or 'N/A'}"
                lbl = Label(text=text, halign="left", valign="middle", size_hint_y=None)
                lbl.bind(texture_size=lbl.setter('size'))
                self.events_box.add_widget(lbl)

        def on_error(req: UrlRequest, error: Any) -> None:
            print(f"Failed to load events: {error}")

        UrlRequest(f"{API_BASE_URL}/calendar", on_success=on_success, on_error=on_error)


class PaymentsScreen(Screen):
    """Stub for handling payments. Implementation will depend on payment provider."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20)
        header = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        back_btn = Button(text="< Back", size_hint=(0.2, 1))
        back_btn.bind(on_release=lambda instance: self.go_home())
        header.add_widget(back_btn)
        header.add_widget(Label(text="Payments", font_size=22))
        layout.add_widget(header)
        layout.add_widget(Label(text="Payment integration is not yet implemented.", size_hint=(1, 0.9)))
        self.add_widget(layout)

    def go_home(self) -> None:
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"


class NotificationsScreen(Screen):
    """Stub for sending notifications via the backend."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20)
        header = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        back_btn = Button(text="< Back", size_hint=(0.2, 1))
        back_btn.bind(on_release=lambda instance: self.go_home())
        header.add_widget(back_btn)
        header.add_widget(Label(text="Notifications", font_size=22))
        layout.add_widget(header)
        layout.add_widget(Label(text="Notification sending is not yet implemented.", size_hint=(1, 0.9)))
        self.add_widget(layout)

    def go_home(self) -> None:
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"


class AboutScreen(Screen):
    """A simple screen describing the photographer and her story."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20)
        header = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        back_btn = Button(text="< Back", size_hint=(0.2, 1))
        back_btn.bind(on_release=lambda instance: self.go_home())
        header.add_widget(back_btn)
        header.add_widget(Label(text="About", font_size=22))
        layout.add_widget(header)
        about_text = (
            "Roberta Gulin is a wedding and family photographer based in Sydney.\n"
            "Through her lens, she captures the love, laughter and special moments\n"
            "that make each session unique. This app showcases her work and \n"
            "provides an easy way for clients to view galleries, check availability,\n"
            "and stay up to date with upcoming shoots."
        )
        content = Label(text=about_text, halign="left", valign="top")
        content.bind(texture_size=content.setter('size'))
        scroll = ScrollView()
        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def go_home(self) -> None:
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"


class RobertaApp(App):
    """Root application class."""

    def build(self) -> ScreenManager:
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(GalleryScreen(name="gallery"))
        sm.add_widget(CalendarScreen(name="calendar"))
        sm.add_widget(PaymentsScreen(name="payments"))
        sm.add_widget(NotificationsScreen(name="notifications"))
        sm.add_widget(AboutScreen(name="about"))
        return sm


if __name__ == "__main__":
    RobertaApp().run()
