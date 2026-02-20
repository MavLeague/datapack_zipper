import flet as ft
import os
import json
from modules.zipper import PackZipper

def insert_to_function(injection_text: str, global_macro: str, reload_functions: list, datapack_path: str, log_callback=None):
    def log(message):
        print(message)
        if log_callback:
            log_callback(message)

    parts = injection_text.split(";")

    for file_info in reload_functions:
        if file_info["macro"]:
            macro = file_info["macro"]
            if len(parts) != macro.count("%s"):
                log(f"Error: Injection Text has {len(parts)} parts, but Macro for {file_info['function']} expects {macro.count('%s')}.")
                continue
        else:
            macro = global_macro
            if len(parts) != macro.count("%s"):
                log(f"Error: Injection Text has {len(parts)} parts, but Global Macro expects {macro.count('%s')}.")
                continue
            

        injection_code = macro % tuple(parts)
        log(f"Generated Command: {injection_code}")
        
        if ":" not in file_info["function"]:
            log(f"Skipping invalid function format: {file_info['function']}")
            continue

        namespace, function_file = file_info["function"].split(":", 1)
        # Construct path: root/data/namespace/functions/file
        full_path = os.path.join(datapack_path, "data", namespace, "function", function_file + ".mcfunction")
        
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Replace line (Line number in config is 1-based)
            if 0 <= file_info["line"] - 1 < len(lines):
                lines[file_info["line"] - 1] = injection_code + "\n"
                
                with open(full_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                log(f"Updated {full_path} at line {file_info['line']}")
            else:
                log(f"Line {file_info['line']} out of bounds in {full_path}")
        else:
            log(f"File not found: {full_path}")


# This class defines your reusable GUI component
class DatapackZipper:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.project_key = "datapack_zipper"
        self.raw_config = {}
        self.config = {}
        self.load_config()
        
        self.zipper = PackZipper()
        self.file_picker = ft.FilePicker()

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.raw_config = json.load(f) or {}

                # If the file already has a project section, use it
                if self.project_key in self.raw_config and isinstance(self.raw_config[self.project_key], dict):
                    self.config = self.raw_config[self.project_key]
                else:
                    # If the file is in the old flat format, migrate those keys under the project key
                    possible_keys = {"datapack_name", "root_folder_path", "target_folder_path", "has_rpack"}
                    if any(k in self.raw_config for k in possible_keys):
                        migrated = {k: self.raw_config.get(k) for k in possible_keys if k in self.raw_config}
                        self.config = migrated
                        # preserve other top-level keys and nest migrated under project key
                        self.raw_config = {k: v for k, v in self.raw_config.items() if k not in migrated}
                        self.raw_config[self.project_key] = migrated
                    else:
                        self.config = {}
            else:
                self.raw_config = {}
                self.config = {}
        except Exception as e:
            print(f"Failed to load config: {e}")
            self.raw_config = {}
            self.config = {}

    def save_config(self):
        data = {
            "datapack_name": (getattr(self, 'datapack_name', None) and self.datapack_name.value) or self.config.get("datapack_name", ""),
            "root_folder_path": (getattr(self, 'root_folder_path', None) and self.root_folder_path.value) or self.config.get("root_folder_path", ""),
            "target_folder_path": (getattr(self, 'target_folder_path', None) and self.target_folder_path.value) or self.config.get("target_folder_path", ""),
            "has_rpack": (getattr(self, 'has_rpack_checkbox', None) and self.has_rpack_checkbox.value) or self.config.get("has_rpack", False),
            "enable_injection": (getattr(self, 'injection_checkbox', None) and self.injection_checkbox.value) or self.config.get("enable_injection", False),
            "injection_text": (getattr(self, 'injection_text_field', None) and self.injection_text_field.value) or self.config.get("injection_text", ""),
            "macro": self.config.get("macro", ""),
            "reload_function": self.config.get("reload_function", [{"function": "my_pack:reload", "line": 1}]),
        }
        try:
            # Load existing raw config to preserve other project sections
            raw = {}
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        raw = json.load(f) or {}
                except Exception:
                    raw = {}

            raw[self.project_key] = data
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False, indent=2)

            self.raw_config = raw
            self.config = data
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def open_config_dialog(self, e):
        try:
            temp_global_macro = [self.config.get("macro", "")]
            selected_row = [None]

            def get_macro_hint(val):
                count = val.count("%s") if val else 0
                return f"Use '%s' as placeholder. Use ; as a divider in the Injection Input when using multiple. Current count: {count}"

            macro_hint = ft.Text(
                value=get_macro_hint(temp_global_macro[0]),
                size=12,
                color=ft.Colors.GREY
            )

            def on_macro_change(e):
                val = e.control.value
                macro_hint.value = get_macro_hint(val)
                macro_hint.update()
                
                if selected_row[0] is None:
                    temp_global_macro[0] = val
                else:
                    selected_row[0].data["macro"] = val

            macro_field = ft.TextField(
                label="Global Macro", 
                value=temp_global_macro[0],
                hint_text="e.g. execute as @a run say %s",
                width=600,
                multiline=True,
                on_change=on_macro_change
            )
            
            reload_list_col = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
            
            def update_edit_icons():
                for row in reload_list_col.controls:
                    if isinstance(row, ft.Row):
                        btn = row.controls[0]
                        if row == selected_row[0]:
                            btn.icon = ft.Icons.EDIT
                        else:
                            btn.icon = ft.Icons.EDIT_OFF
                reload_list_col.update()

            def select_entry(row):
                if selected_row[0] == row:
                    # Deselect
                    selected_row[0] = None
                    macro_field.label = "Global Macro"
                    macro_field.value = temp_global_macro[0]
                else:
                    # Select
                    selected_row[0] = row
                    macro_field.label = "Entry Macro"
                    macro_field.value = row.data.get("macro", "")
                
                macro_field.update()
                macro_hint.value = get_macro_hint(macro_field.value)
                macro_hint.update()
                update_edit_icons()

            def delete_entry(row):
                if selected_row[0] == row:
                    selected_row[0] = None
                    macro_field.label = "Global Macro"
                    macro_field.value = temp_global_macro[0]
                    macro_field.update()
                    macro_hint.value = get_macro_hint(macro_field.value)
                    macro_hint.update()

                reload_list_col.controls.remove(row)
                reload_list_col.update()

            def add_entry(data=None, update_ui=True):
                if data is None:
                    data = {"function": "", "line": 1, "macro": ""}
                
                if "macro" not in data:
                    data["macro"] = ""
                
                row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                
                edit_btn = ft.IconButton(ft.Icons.EDIT_OFF, tooltip="Edit Macro", on_click=lambda e: select_entry(row))
                fn_field = ft.TextField(value=data.get("function", ""), label="Function", expand=True, height=40, content_padding=10, text_size=14)
                line_field = ft.TextField(value=str(data.get("line", 1)), label="Line", width=60, height=40, keyboard_type=ft.KeyboardType.NUMBER, content_padding=10, text_size=14)
                delete_btn = ft.IconButton(ft.Icons.DELETE, on_click=lambda e: delete_entry(row))
                
                row.controls = [edit_btn, fn_field, line_field, delete_btn]
                row.data = data
                
                reload_list_col.controls.append(row)
                if update_ui:
                    reload_list_col.update()

            current_entries = self.config.get("reload_function", [{"function": "my_pack:reload", "line": 1, "macro": ""}])
            if not isinstance(current_entries, list):
                current_entries = []
                
            for entry in current_entries:
                add_entry(entry, update_ui=False)

            def save_close(e):
                self.config["macro"] = temp_global_macro[0]
                
                new_list = []
                for row in reload_list_col.controls:
                    if isinstance(row, ft.Row) and len(row.controls) >= 3:
                        fn_val = row.controls[1].value
                        line_val = row.controls[2].value
                        macro_val = row.data.get("macro", "")
                        try:
                            line_int = int(line_val)
                        except ValueError:
                            line_int = 1
                        
                        if fn_val:
                            new_list.append({"function": fn_val, "line": line_int, "macro": macro_val})
                
                self.config["reload_function"] = new_list
                self.save_config()
                dlg.open = False
                e.page.update()

            def close(e):
                dlg.open = False
                e.page.update()

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Configure Function Injection"),
                content=ft.Container(
                    width=600,
                    height=400,
                    content=ft.Column([
                        macro_field,
                        macro_hint,
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Reload Functions", size=16, weight=ft.FontWeight.BOLD),
                            ft.IconButton(ft.Icons.ADD, on_click=lambda e: add_entry())
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(
                            content=reload_list_col,
                            border=ft.Border.all(1, ft.Colors.GREY),
                            border_radius=5,
                            padding=5,
                            expand=True
                        ),
                        ft.Text("Don't forget to provide a namespace! (Don't add .mcfunction)")
                    ])
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=close),
                    ft.TextButton("Save", on_click=save_close),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                on_dismiss=lambda e: print("Dialog closed"),
            )
            
            e.page.show_dialog(dlg)
            e.page.update()
            print("Config dialog opened.")
        except Exception as ex:
            print(f"Error opening config dialog: {ex}")

    def create_ui(self):
        # Text fields for ID and name (pre-fill from config if available)
        self.datapack_name = ft.TextField(
            label="Datapack Name",
            width=300,
            value=self.config.get("datapack_name", ""),
            on_change=lambda e: self.save_config(),
        )
        
        def toggle_injection_text(e):
            self.injection_text_field.visible = self.injection_checkbox.value
            self.injection_text_field.update()
            self.save_config()

        def on_path_change(e):
            e.control.tooltip = e.control.value
            e.control.update()
            self.save_config()

        self.root_folder_path = ft.TextField(
            label="Datapack Folder",
            width=300,
            value=self.config.get("root_folder_path", ""),
            tooltip=self.config.get("root_folder_path", ""),
            on_change=on_path_change,
        )

        self.target_folder_path = ft.TextField(
            label="Export Folder",
            width=300,
            value=self.config.get("target_folder_path", ""),
            tooltip=self.config.get("target_folder_path", ""),
            on_change=on_path_change,
        )

        self.has_rpack_checkbox = ft.Checkbox(
            label="Include Resource Pack",
            value=self.config.get("has_rpack", False),
            on_change=lambda e: self.save_config(),
        )

        self.injection_checkbox = ft.Checkbox(
            label="Enable Injection",
            value=self.config.get("enable_injection", False),
            on_change=toggle_injection_text,
        )
        
        config_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip="Configure Injection Settings",
            on_click=self.open_config_dialog
        )
        
        self.injection_text_field = ft.TextField(
            label="Injection Text",
            width=300,
            value=self.config.get("injection_text", ""),
            on_change=lambda e: self.save_config(),
            visible=self.config.get("enable_injection", False),
        )

        create_button = ft.Button("Zip Datapack!", on_click=self.create_zip)
        injection_button = ft.Button("Inject into Function", on_click=self.inject_function_trigger)
        root_choose_button = ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=self.on_root_folder_picked)
        target_choose_button = ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=self.on_target_folder_picked)

        # Main layout
        return ft.Column(
            [
                #self.root_folder_picker,
                #self.target_folder_picker,
                self.datapack_name,
                ft.Row([self.root_folder_path, root_choose_button]),
                ft.Row([self.target_folder_path, target_choose_button]),
                self.has_rpack_checkbox,
                ft.Row([self.injection_checkbox, config_btn]),
                self.injection_text_field,
                ft.Row([create_button, injection_button]),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=15,
        )
        
    def did_mount(self):
        self.page.overlay.append(self.file_picker)
        self.page.update()
        
    
    async def on_root_folder_picked(self, e: ft.Event[ft.Button]):
        path = await self.file_picker.get_directory_path()
        if path is not None:
            self.root_folder_path.value = path
            self.root_folder_path.tooltip = path
            self.root_folder_path.update()
            self.save_config()
            
    async def on_target_folder_picked(self, e: ft.Event[ft.Button]):
        path = await self.file_picker.get_directory_path()
        if path is not None:
            self.target_folder_path.value = path
            self.target_folder_path.tooltip = path
            self.target_folder_path.update()
            self.save_config()
            
    def inject_function_trigger(self, e):
        
        feed = ft.Column([ft.Text("Inserting into Functions...")], height=150, width=600, scroll=ft.ScrollMode.AUTO)
        
        def close_dlg(e):
            info_popup.open = False
            e.page.update()

        info_popup = ft.AlertDialog(
            title=ft.Text("Inserted"),
            content=feed,
            actions=[ft.TextButton("Okay", on_click=close_dlg)],
            modal=True,
        )
        
        e.page.show_dialog(info_popup)
        e.page.update()
        
        print("--- Injecting text to pack ---\n")
        if self.injection_checkbox.value:
            if not self.injection_text_field.value:
                feed.controls.append(ft.Text("Error: Please enter injection text."))
                info_popup.update()
                e.page.update()
                return
            
            def log_to_feed(msg):
                feed.controls.append(ft.Text(msg))
                info_popup.update()

            insert_to_function(self.injection_text_field.value, self.config.get("macro"), self.config.get("reload_function"), self.root_folder_path.value, log_callback=log_to_feed)
    
    def create_zip(self, e):
        
        feed = ft.Column([ft.Text("Creating datapack zip...")], height=150, scroll=ft.ScrollMode.AUTO)
        
        def close_dlg(e):
            info_popup.open = False
            e.page.update()

        info_popup = ft.AlertDialog(
            title=ft.Text("Zip Created"),
            content=feed,
            actions=[ft.TextButton("Okay", on_click=close_dlg)],
            modal=True,
        )
        
        e.page.show_dialog(info_popup)
        e.page.update()
        
        print("--- Creating datapack zip... ---\n")
        root_folder = self.root_folder_path.value
        if not root_folder:
            feed.controls.append(ft.Text("Error: Please choose a datapack folder."))
            info_popup.update()
            e.page.update()
            return
        
        target_folder = self.target_folder_path.value
        if not target_folder:
            feed.controls.append(ft.Text("Error: Please choose an export folder."))
            info_popup.update()
            e.page.update()
            return
        
        datapack_name = self.datapack_name.value
        if not datapack_name:
            feed.controls.append(ft.Text("Error: Please enter a datapack name."))
            info_popup.update()
            e.page.update()
            return
        
        # List of permitted file extensions
        allowed_extensions = ['.json', '.mcmeta', '.png', '.nbt', '.mcfunction', '.ogg', '.fsh', '.vsh']

        datapack_zip_filename = os.path.join(target_folder, f"{datapack_name}.zip")
        
        self.zipper.zip_datapack(root_folder, datapack_zip_filename, allowed_extensions=allowed_extensions)

        # Save current settings after creating the zip
        self.save_config()
        print(f"Datapack zip created: {datapack_zip_filename}")

        feed.controls.append(ft.Text(f"Datapack zip created: {datapack_zip_filename}"))
        info_popup.update()
        e.page.update()

        if self.has_rpack_checkbox.value:
            feed.controls.append(ft.Text("Creating resource pack zip..."))
            info_popup.update()
            resource_zip_filename = os.path.join(target_folder, f"{datapack_name}_resources.zip")
            
            self.zipper.zip_resourcepack(root_folder, resource_zip_filename, allowed_extensions=allowed_extensions)

            print(f"Resource pack zip created: {resource_zip_filename}")
            feed.controls.append(ft.Text(f"Resource pack zip created: {resource_zip_filename}"))
            info_popup.update()
            e.page.update()

            # Save settings as well
            self.save_config()

def main(page: ft.Page):
    page.title = "Datapack Zipper"
    fg = DatapackZipper()
    page.add(fg.create_ui())


if __name__ == "__main__":
    ft.run(main)
