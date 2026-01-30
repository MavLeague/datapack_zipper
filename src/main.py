import flet as ft
from datapack_zipper import DatapackZipper
from resource_sync import ResourceSync
from modules.console import ConsoleOutput
import webbrowser
import sys
import toml

def make_section(title, content, icon=None, width=None, height=None):
    header = ft.Row(
        [icon, ft.Text(title, size=18, weight=ft.FontWeight.BOLD)]
        if icon is not None
        else [ft.Text(title, size=18, weight=ft.FontWeight.BOLD)]
    )

    # Only expand content if a fixed height is provided
    should_expand = height is not None

    return ft.Card(
        width=width,
        height=height,
        elevation=1,
        content=ft.Container(
            padding=10,
            content=ft.Column(
                [
                    header,
                    ft.Column(
                        [content],
                        expand=should_expand
                    )
                ],
                spacing=10,
                expand=should_expand
            )
        )
    )

def main(page: ft.Page):
    page.title = "Datapack Manager"
    
    # load data from toml
    config = toml.load("pyproject.toml")
    v_name = config["project"]["version"]
    
    # Initialize console and hide
    console = ConsoleOutput()
    console.visible = False
    sys.stdout = console # Redirect print output

    def open_info(e):
        def toggle_console(e):
            console.visible = not console.visible
            console.update()

        info = ft.AlertDialog(
            modal=False,
            title=ft.Text("About this Program"),
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.INFO),ft.Text(f"Flet Version: {ft.__version__}\nCurrent Build: {v_name}")]),
                ft.Row([ft.Icon(ft.Icons.BUG_REPORT),ft.Button(f"Report Issue", on_click=lambda _: webbrowser.open("https://github.com/MavLeague/datapack_zipper/issues", new=0, autoraise=True))]),
                ft.Row([ft.Icon(ft.Icons.CODE),ft.Button("Toggle Console", on_click=toggle_console)])
            ], height=150)
        )
        page.show_dialog(info)

    # Other GUI parts could be here
    header = ft.Row([ft.IconButton(ft.Icons.INFO, on_click=open_info),ft.Text("Datapack Manager", size=24, weight=ft.FontWeight.BOLD)])
    datapack_module = DatapackZipper()
    sync_module = ResourceSync()
    
    page.add(
        header,
        ft.Row([
            make_section(
                "Datapack Zipper",
                datapack_module.create_ui(),
                ft.Icon(ft.Icons.FOLDER_ZIP,color=ft.Colors.WHITE)
            ),
            make_section(
                "Sync Resourcepack",
                sync_module.create_ui(),
                ft.Icon(ft.Icons.FOLDER_ZIP,color=ft.Colors.WHITE)
            )
        ]),
        console
    )
    
"""
    # Calculate the sum height of all objects on the page
    total_height = 0
    for control in page.controls:
        if hasattr(control, "height") and control.height:
            total_height += control.height
        elif isinstance(control, ft.Row):
            # For rows, take the max height of children (e.g. the Card)
            total_height += max((c.height for c in control.controls if hasattr(c, "height") and c.height), default=0)
        elif isinstance(control, ft.Text):
            total_height += (control.size or 16) * 1.5  # Estimate text height
        total_height += 10  # Add spacing

    page.window.min_height = total_height + 40  # Add window padding
    page.window.height = page.window.min_height
"""

if __name__ == "__main__":
    ft.run(main)
