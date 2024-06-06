from ieee_2030_5_gui.views.server_control import server_control_view
from ieee_2030_5_gui.views.show_resource_tree import show_resource_tree_view
from ieee_2030_5_gui.views.home import home_view
from pydantic import BaseModel, ConfigDict
from typing import Optional, Callable
import flet as ft

class _2030_5View(BaseModel):
    #model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)
    route: str
    instance: object

class _2030_5Views(BaseModel):
    home: _2030_5View = _2030_5View(route="/", instance=home_view)
    server_control: _2030_5View = _2030_5View(route="/server_control", instance=server_control_view)
    show_tree: _2030_5View = _2030_5View(route="/show_tree", instance=show_resource_tree_view)

    def __getitem__(self, item):
        return getattr(self, item)

    def __iter__(self):
        for page in self.__dict__.values():
            yield page

AppViews = _2030_5Views()
