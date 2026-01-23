import flet as ft
import os
import zipfile
import json

# Zipping functions
def add_folder_to_zip(zf: zipfile.ZipFile, folder_path: str, arc_folder_name: str = None, allowed_extensions: list = None):

    if arc_folder_name is None:
        arc_folder_name = os.path.basename(folder_path)
    
    print(f"Adding folder '{folder_path}' as '{arc_folder_name}'...")
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if allowed_extensions:
                _, ext = os.path.splitext(file)
                if ext.lower() not in allowed_extensions:
                    continue

            file_path = os.path.join(root, file)
            
            relative_path = os.path.relpath(file_path, folder_path)
            
            arcname = os.path.join(arc_folder_name, relative_path)
            
            print(f"  > {file_path}  ->  {arcname}")
            zf.write(file_path, arcname=arcname)

def verify_zip(zip_filename: str):
    """Prints the contents of the created zip file for verification."""
    print(f"\n--- Verifying contents of '{zip_filename}' ---")
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zf:
            zf.printdir()
    except FileNotFoundError:
        print(f"Error: '{zip_filename}' not found.")
    except zipfile.BadZipFile:
        print(f"Error: '{zip_filename}' is not a valid zip file.")
        
def get_version_folders(pack_path: str):
    """Extracts version folders from the pack.mcmeta file."""
    version_folders = []
    try:
        with open(pack_path, "r", encoding="utf-8") as f:
            content = json.load(f)
            
            overlays = content.get("overlays", {})
            entries = overlays.get("entries", [])
            
            for entry in entries:
                directory = entry.get("directory")
                if directory:
                    version_folders.append(directory)
                
    except Exception as e:
        print(f"Error reading pack.mcmeta: {e} has no overlays?")
    return version_folders

def insert_version(version_text: str, version_macro: str, reload_functions: list, datapack_path: str):
    parts = version_text.split(";")
    if len(parts) != version_macro.count("%s"):
        print(f"Error: version_text has {len(parts)} parts, but version_macro expects {version_macro.count('%s')}.")
        return

    version_code = version_macro % tuple(parts)
    print(f"Generated Command: {version_code}")
    
    for file_info in reload_functions:
        if ":" not in file_info["function"]:
            print(f"Skipping invalid function format: {file_info['function']}")
            continue

        namespace, function_file = file_info["function"].split(":", 1)
        # Construct path: root/data/namespace/functions/file
        full_path = os.path.join(datapack_path, "data", namespace, "function", function_file)
        
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Replace line (Line number in config is 1-based)
            if 0 <= file_info["line"] - 1 < len(lines):
                lines[file_info["line"] - 1] = version_code + "\n"
                
                with open(full_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                print(f"Updated {full_path} at line {file_info['line']}")
            else:
                print(f"Line {file_info['line']} out of bounds in {full_path}")
        else:
            print(f"File not found: {full_path}")


# This class defines your reusable GUI component
class DatapackZipper:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.project_key = "datapack_zipper"
        self.raw_config = {}
        self.config = {}
        self.load_config()

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
            "insert_version": (getattr(self, 'version_checkbox', None) and self.version_checkbox.value) or self.config.get("insert_version", False),
            "version_text": (getattr(self, 'version_text', None) and self.version_text.value) or self.config.get("version_text", ""),
            "version_macro": (getattr(self, 'version_macro', None) and self.version_macro.value) or self.config.get("version_macro", ""),
            "reload_function": (getattr(self, 'reload_function', None) and self.reload_function.value) or self.config.get("reload_function", [{"function": "reload.mcfunction", "line": 1}]),
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
            def get_macro_hint(val):
                count = val.count("%s") if val else 0
                return f"Use '%s' as placeholder. Use ; as a divider in the Version Input when using multiple. Current count: {count}"

            macro_hint = ft.Text(
                value=get_macro_hint(self.config.get("version_macro", "")),
                size=12,
                color=ft.Colors.GREY
            )

            def on_macro_change(e):
                macro_hint.value = get_macro_hint(e.control.value)
                macro_hint.update()

            macro_field = ft.TextField(
                label="Version Macro", 
                value=self.config.get("version_macro", ""),
                hint_text="e.g. command %s",
                on_change=on_macro_change
            )
            
            reload_list_col = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
            
            def delete_entry(row):
                reload_list_col.controls.remove(row)
                reload_list_col.update()

            def add_entry(data=None, update_ui=True):
                if data is None:
                    data = {"function": "", "line": 1}
                
                fn_field = ft.TextField(value=data.get("function", ""), label="Function", expand=True, height=40, content_padding=10, text_size=14)
                line_field = ft.TextField(value=str(data.get("line", 1)), label="Line", width=60, height=40, keyboard_type=ft.KeyboardType.NUMBER, content_padding=10, text_size=14)
                
                delete_btn = ft.IconButton(ft.Icons.DELETE)
                
                row = ft.Row([
                    fn_field,
                    line_field,
                    delete_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                
                delete_btn.on_click = lambda e: delete_entry(row)
                
                reload_list_col.controls.append(row)
                if update_ui:
                    reload_list_col.update()

            current_entries = self.config.get("reload_function", [{"function": "reload.mcfunction", "line": 1}])
            if not isinstance(current_entries, list):
                current_entries = []
                
            for entry in current_entries:
                add_entry(entry, update_ui=False)

            def save_close(e):
                self.config["version_macro"] = macro_field.value
                
                new_list = []
                for row in reload_list_col.controls:
                    if isinstance(row, ft.Row) and len(row.controls) >= 2:
                        fn_val = row.controls[0].value
                        line_val = row.controls[1].value
                        try:
                            line_int = int(line_val)
                        except ValueError:
                            line_int = 1
                        
                        if fn_val:
                            new_list.append({"function": fn_val, "line": line_int})
                
                self.config["reload_function"] = new_list
                self.save_config()
                dlg.open = False
                e.page.update()

            def close(e):
                dlg.open = False
                e.page.update()

            dlg = ft.AlertDialog(
                title=ft.Text("Version Configuration"),
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
                        )
                    ])
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=close),
                    ft.TextButton("Save", on_click=save_close),
                ],
            )
            
            e.page.dialog = dlg
            dlg.open = True
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
        
        def toggle_version_text(e):
            self.version_text.visible = self.version_checkbox.value
            self.version_text.update()
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

        self.version_checkbox = ft.Checkbox(
            label="Insert Version",
            value=self.config.get("insert_version", False),
            on_change=toggle_version_text,
        )
        
        config_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip="Configure Version Settings",
            on_click=self.open_config_dialog
        )
        
        self.version_text = ft.TextField(
            label="Version",
            width=300,
            value=self.config.get("version_text", ""),
            on_change=lambda e: self.save_config(),
            visible=self.config.get("insert_version", False),
        )

        create_button = ft.Button("Zip Datapack!", on_click=self.create_zip)
        version_button = ft.Button("Insert Version", on_click=self.insert_version_trigger)
        root_choose_button = ft.Button("Browse", on_click=self.on_root_folder_picked)
        target_choose_button = ft.Button("Browse", on_click=self.on_target_folder_picked)

        # Main layout
        return ft.Column(
            [
                #self.root_folder_picker,
                #self.target_folder_picker,
                self.datapack_name,
                ft.Row([self.root_folder_path, root_choose_button]),
                ft.Row([self.target_folder_path, target_choose_button]),
                self.has_rpack_checkbox,
                ft.Row([self.version_checkbox, config_btn]),
                self.version_text,
                ft.Row([create_button, version_button]),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=15,
        )
        
    async def on_root_folder_picked(self, e: ft.Event[ft.Button]):
        path = await ft.FilePicker().get_directory_path()
        if path is not None:
            self.root_folder_path.value = path
            self.root_folder_path.tooltip = path
            self.root_folder_path.update()
            self.save_config()
            
    async def on_target_folder_picked(self, e: ft.Event[ft.Button]):
        path = await ft.FilePicker().get_directory_path()
        if path is not None:
            self.target_folder_path.value = path
            self.target_folder_path.tooltip = path
            self.target_folder_path.update()
            self.save_config()
            
    def insert_version_trigger(self, e):
        print("--- Inserting Version text to pack ---\n")
        if self.version_checkbox.value:
            if not self.version_text.value:
                e.page.snack_bar = ft.SnackBar(ft.Text("Please enter a version."))
                e.page.snack_bar.open = True
                e.page.update()
                return
            
            insert_version(self.version_text.value, self.config.get("version_macro"), self.config.get("reload_function"), self.root_folder_path.value)
    
    def create_zip(self, e):
        print("--- Creating datapack zip... ---\n")
        root_folder = self.root_folder_path.value
        if not root_folder:
            e.page.snack_bar = ft.SnackBar(ft.Text("Please choose a datapack folder."))
            e.page.snack_bar.open = True
            e.page.update()
            return
        
        target_folder = self.target_folder_path.value
        if not target_folder:
            e.page.snack_bar = ft.SnackBar(ft.Text("Please choose an export folder."))
            e.page.snack_bar.open = True
            e.page.update()
            return
        
        datapack_name = self.datapack_name.value
        if not datapack_name:
            e.page.snack_bar = ft.SnackBar(ft.Text("Please enter a datapack name."))
            e.page.snack_bar.open = True
            e.page.update()
            return
        
        # List of permitted file extensions
        allowed_extensions = ['.json', '.mcmeta', '.png', '.nbt', '.mcfunction', '.ogg', '.fsh', '.vsh']

        datapack_zip_filename = os.path.join(target_folder, f"{datapack_name}.zip")
        
        with zipfile.ZipFile(datapack_zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            add_folder_to_zip(zf, os.path.join(root_folder, "data"), arc_folder_name="data", allowed_extensions=allowed_extensions)
            
            # add version folders from overlays
            version_folders = get_version_folders(os.path.join(root_folder, "pack.mcmeta"))
            if not version_folders == []:
                for folder in version_folders:
                    add_folder_to_zip(zf, os.path.join(root_folder, folder, "data"), arc_folder_name=f"{folder}/data", allowed_extensions=allowed_extensions)
            
            # write pack.mcmeta and icon
            zf.write(os.path.join(root_folder, "pack.mcmeta"), arcname="pack.mcmeta")
            zf.write(os.path.join(root_folder, "pack.png"), arcname="pack.png")
        # Save current settings after creating the zip
        self.save_config()
        print(f"Datapack zip created: {datapack_zip_filename}")

        if self.has_rpack_checkbox.value:
            resource_zip_filename = os.path.join(target_folder, f"{datapack_name}_resources.zip")
            
            with zipfile.ZipFile(resource_zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
                add_folder_to_zip(zf, os.path.join(root_folder, "assets"), arc_folder_name="assets", allowed_extensions=allowed_extensions)
                
                # Choose which resource pack meta file to include (try both valid names)
                for candidate in ("resource_pack.mcmeta", "pack_resourcepack.mcmeta"):
                    candidate_path = os.path.join(root_folder, candidate)
                    if os.path.exists(candidate_path):
                        # add version folders from overlays
                        version_folders = get_version_folders(candidate_path)
                        if not version_folders == []:
                            for folder in version_folders:
                                add_folder_to_zip(zf, os.path.join(root_folder, folder, "assets"), arc_folder_name=f"{folder}/assets", allowed_extensions=allowed_extensions)
                        
                        # write pack.mcmeta
                        zf.write(candidate_path, arcname="pack.mcmeta")
                        break
                else:
                    print("No resource pack metadata file found (tried resource_pack.mcmeta, pack_resourcepack.mcmeta).")
                zf.write(os.path.join(root_folder, "pack.png"), arcname="pack.png")
                
            print(f"resource pack zip created: {resource_zip_filename}")
            # Save settings as well
            self.save_config()

def main(page: ft.Page):
    page.title = "Datapack Zipper"
    fg = DatapackZipper()
    page.add(fg.create_ui())


if __name__ == "__main__":
    ft.app(target=main)
