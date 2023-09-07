from fastapi import FastAPI
from nicegui import ui

from .pages.certs import show_certs
from .pages.controls import show_controls


def init(fastapi_app: FastAPI) -> None:
    
    @fastapi_app.get("/admin/cert")
    
    # @ui.page('/show')
    # def show():
    #     ui.label('Hello, FastAPI!')

    #     # NOTE dark mode will be persistent for each user across tabs and server restarts
    #     ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
    #     ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')

    ui.run_with(
        fastapi_app,
        storage_secret='pick your private secret here',  # NOTE setting a secret is optional but allows for persistent storage per user
    )