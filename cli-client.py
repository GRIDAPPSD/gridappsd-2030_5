import textual
import yaml
from textual.app import App
from textual.widget import Widget
from textual.widgets import TreeItem, TreeWidget


class MyTreeWidget(TreeWidget):

    def __init__(self, data):
        super().__init__(data)

        # Create the root node of the tree
        root = TreeItem(text="Root", expanded=True)
        self.add_top_level_item(root)

        # Recursively add child nodes to the root node
        self._add_child_items(root, data)

    def _add_child_items(self, parent_node, data):
        # Loop through the keys and values in the current data object
        for key, value in data.items():
            # Create a new TreeItem for the current key
            item = TreeItem(text=key)

            # If the current value is a dictionary, recursively add its child nodes
            if isinstance(value, dict):
                self._add_child_items(item, value)

            # Add the new TreeItem to the parent node
            parent_node.add_child_item(item)


class MyTreeWidgetContainer(Widget):

    def __init__(self, data):
        super().__init__()
        self.tree_widget = MyTreeWidget(data)
        self.add_subview(self.tree_widget)


class MyCLIApp(App):

    async def on_load(self, event):
        # Load the data from the YAML file
        with open("my_data.yaml") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)

        # Create the tree widget container and add it to the app
        tree_widget_container = MyTreeWidgetContainer(data)
        self.add_root_widget(tree_widget_container)


MyCLIApp.run()
