import flet as ft

from typing import Callable

import logging
import os
from pathlib import Path
from fastapi.middleware.wsgi import WSGIMiddleware

_log = logging.getLogger(__name__)

start_button: ft.Ref[ft.ElevatedButton] = ft.Ref()
stop_button: ft.Ref[ft.ElevatedButton] = ft.Ref()
this_view: ft.Ref[ft.View] = ft.Ref()
this_page: ft.Ref[ft.Page] = ft.Ref()



def start_server() -> None:
    _log.debug("Starting server")
    from ieee_2030_5_gui.__main__ import app
    from ieee_2030_5.flask_server import make_app

    config_file = Path(os.environ["CONFIG_FILE"])
    reset_certs = bool(os.environ.get("RESET_CERTS", False))
    flask_app = make_app(config_file=config_file, reset_certs=reset_certs)

    app.mount("/api",
              WSGIMiddleware(flask_app))

    start_button.current.disabled = True
    stop_button.current.disabled = False
    this_view.current.update()


    # app.run(host=os.getenv(f"{PREFIX}_HOST"), port=os.getenv(f"{PREFIX}_PORT"), debug=True, ssl_context=(os.getenv(f"{PREFIX}_CLIENT_CERT"), os.getenv(f"{PREFIX}_CLIENT_KEY"), os.getenv(f"{PREFIX}_CA_CERT")))
    # app.run(host=os.getenv(f"{PREFIX}_HOST"), port=os.getenv(f"{PREFIX}_PORT"), debug=True, ssl_context=(os.getenv(f"{PREFIX}_CLIENT_CERT"), os.getenv(f"{PREFIX}_CLIENT_KEY"), os.getenv(f"{PREFIX}_CA_CERT"))

def stop_server() -> None:
    _log.debug("Stopping server")
    app.unmount("/api")
    start_button.current.disabled = False
    stop_button.current.disabled = True
    this_view.current.update()

def server_control_view(page: ft.Page) -> ft.View:
    this_page.current = page

    this_view.current = ft.View("/", [
        ft.AppBar(title=ft.Text("Server Control"),
               automatically_imply_leading=False,
               bgcolor=ft.colors.SURFACE_VARIANT),
        ft.ElevatedButton("Start Server", ref=start_button, on_click=lambda _: start_server()),
        ft.ElevatedButton("Stop Server", disabled=True, ref=stop_button, on_click=lambda _: stop_server()),
    ])

    return this_view.current
