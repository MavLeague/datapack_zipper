import flet as ft
import sys
import time

class ConsoleOutput(ft.Container):
    def __init__(self):
        super().__init__()
        # The list that holds our log lines
        self.console_view = ft.ListView(
            expand=True,
            spacing=0,
            auto_scroll=True,
        )
        # The container that looks like a terminal
        self.content = self.console_view
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = 5
        self.padding = 10
        self.expand = True
        self.height = 300 # Fixed height or expand=True
        self.border = ft.Border.all(1, ft.Colors.GREY_800)

    def write(self, text):
        if text.strip():  # Prevents unnecessary empty lines
            self.console_view.controls.append(
                ft.Text(
                    text.strip(),
                    color=ft.Colors.GREEN_ACCENT_400,
                    font_family="Consolas", # Monospace font for terminal look
                    size=12,
                )
            )
            self.update()

    def flush(self):
        # Required by sys.stdout
        pass
    
def main(page: ft.Page):
    page.title = "Flet Terminal UI"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Instance of our console
    console = ConsoleOutput()

    # Redirect sys.stdout
    sys.stdout = console

    def button_click(e):
        print(f"Button clicked at {time.strftime('%H:%M:%S')}")
        print("This is a simulated console output...")

    page.add(
        ft.Text("Example Console Interface", size=20, weight="bold"),
        ft.Button("Generate Log", on_click=button_click),
        ft.Divider(),
        ft.Text("Console:"),
        console # Here we bind the terminal window
    )

if __name__ == "__main__":
    ft.run(main)
