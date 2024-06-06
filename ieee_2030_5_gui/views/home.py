import flet as ft

from typing import Callable

import logging

_log = logging.getLogger(__name__)


def home_view(page: ft.Page) -> ft.View:
    return ft.View(
        "/",
        [
            ft.AppBar(title=ft.Text("2030.5 GUI"),
                      automatically_imply_leading=False,
                      bgcolor=ft.colors.SURFACE_VARIANT),
            ft.ElevatedButton("Server Control", on_click=lambda _: page.go("/server_control")),
            ft.ElevatedButton("Show List Tree", on_click=lambda _: page.go("/show_tree")),
    #ElevatedButton("Subscriber App", on_click=lambda _: page.go("/subscriber")),
        ])
