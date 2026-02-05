import flet as ft
import os
import json
from modules.folder_sync import SyncManager

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


class ResourceSync:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.project_key = "resource_sync"
        self.raw_config = {}
        self.config = {}
        self.load_config()
        
        self.manager = SyncManager()
        self.syncronizing = False
        self.file_picker = ft.FilePicker()

    def did_mount(self):
        self.page.overlay.append(self.file_picker)
        self.page.update()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.raw_config = json.load(f) or {}

                if self.project_key in self.raw_config and isinstance(self.raw_config[self.project_key], dict):
                    self.config = self.raw_config[self.project_key]
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
        # Define the fields you want to save here
        data = {
            "minecraft_path": (getattr(self, 'minecraft_path', None) and self.minecraft_path.value) or self.config.get("minecraft_path", ""),
            "sync_entries": []
        }
        
        if hasattr(self, 'entries_column'):
            for row in self.entries_column.controls:
                if isinstance(row, ft.Row) and len(row.controls) > 0:
                    data["sync_entries"].append({
                        "name": row.controls[0].value,
                        "paused": row.data
                    })
        else:
            data["sync_entries"] = self.config.get("sync_entries", [])

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
    
    async def on_minecraft_path_picked(self, e: ft.Event[ft.Button]):
        path = await self.file_picker.get_directory_path()
        if path is not None:
            self.minecraft_path.value = path
            self.minecraft_path.tooltip = path
            self.minecraft_path.update()
            self.save_config()

    def create_ui(self):
        # Define your UI components here
        def on_path_change(e):
            e.control.tooltip = e.control.value
            e.control.update()
            self.save_config()

        self.minecraft_path = ft.TextField(
            label="Minecraft Game Path",
            width=300,
            value=self.config.get("minecraft_path", ""),
            tooltip=self.config.get("minecraft_path", ""),
            on_change=on_path_change,
        )
       
        minecraft_browse_btn = ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=self.on_minecraft_path_picked)
        
        self.entries_column = ft.Column(spacing=10)
        
        for entry in self.config.get("sync_entries", []):
            self.add_entry_row(entry, update_ui=False)

        add_btn = ft.Button("Reload List", icon=ft.Icons.REFRESH, on_click=self.reload_list)
        self.sync_button = ft.Button("Sync Now", on_click=self.run_sync)

        # Main layout
        return ft.Column(
            [
                ft.Row([self.minecraft_path, minecraft_browse_btn]),
                ft.Row([
                    ft.Card(
                        elevation=2,
                        content=ft.Container(
                            padding=10,
                            content=ft.Column([
                                ft.Text("Synched Packs:", weight=ft.FontWeight.BOLD, size=25),
                                self.entries_column,
                                add_btn,
                            ])
                        )
                    )
                ]),
                self.sync_button,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=15,
        )

    def add_entry_row(self, value="", update_ui=True):
        name = value
        paused = False
        if isinstance(value, dict):
            name = value.get("name", "")
            paused = value.get("paused", False)
            
        tf = ft.Text(value=name, key="name", width=220)
        
        def delete_entry(e):
            self.entries_column.controls.remove(row)
            self.entries_column.update()
            self.save_config()
            
        def toggle_pause(e):
            if not self.syncronizing:
                row.data = not row.data
                e.control.icon = ft.Icons.PLAY_ARROW if row.data else ft.Icons.PAUSE
                e.control.tooltip = "Resume Sync" if row.data else "Pause Sync"
                e.control.update()
                self.save_config()

        action_btn = ft.IconButton(ft.Icons.PLAY_ARROW if paused else ft.Icons.PAUSE, tooltip="Resume Sync" if paused else "Pause Sync", on_click=toggle_pause, key="pause")
        delete_btn = ft.IconButton(ft.Icons.DELETE, tooltip="Delete", on_click=delete_entry)
        
        row = ft.Row([tf, action_btn, delete_btn])
        row.data = paused # False = Active, True = Paused
        self.entries_column.controls.append(row)
        
        if update_ui:
            self.entries_column.update()
            self.save_config()

    def reload_list(self, e):
        self.entries_column.controls.clear()
        if os.path.exists(os.path.join(self.minecraft_path.value, "datapacks")):
            for datapack in os.listdir(os.path.join(self.minecraft_path.value, "datapacks")):
                print(datapack)
                if os.path.exists(os.path.join(self.minecraft_path.value, "datapacks", datapack, "assets")):
                    self.add_entry_row(value=datapack)
                    print(f"{datapack} added!")
                else:
                    print(f"{datapack} skipped...")
        else:
            print(f"Your Minecraft Folder doesn't contain a Folder called \"datapacks\".")
        
    
    def add_list2manager(self):
        
        self.manager.clear()
        
        datapack_folder = os.path.join(self.minecraft_path.value, "datapacks")
        resourcepack_folder = os.path.join(self.minecraft_path.value, "resourcepacks")
        
        for row_control in self.entries_column.controls:
            if isinstance(row_control, ft.Row):
                if not row_control.data:
                    datapack_name = row_control.controls[0].value
                    source_folder = os.path.join(datapack_folder, datapack_name)
                    target_folder = os.path.join(resourcepack_folder, datapack_name)
                    
                    # add assets
                    self.manager.add_sync_pair(os.path.join(source_folder, "assets"), os.path.join(target_folder, "assets"))
                    
                    # add Overlays
                    version_folders = get_version_folders(os.path.join(source_folder, "resource_pack.mcmeta"))
                    if not version_folders == []:
                        for folder in version_folders:
                            self.manager.add_sync_pair(os.path.join(source_folder, folder, "assets"), os.path.join(target_folder, folder, "assets"))
                            
                    # add files
                    self.manager.add_single_file_sync(os.path.join(source_folder, "resource_pack.mcmeta"), os.path.join(target_folder, "pack.mcmeta"))
                    self.manager.add_single_file_sync(os.path.join(source_folder, "pack.png"), os.path.join(target_folder, "pack.png"))

                
                
    
            
    def run_sync(self, e):
                
        if not self.syncronizing:
            try:
                self.syncronizing = True
                self.sync_button.content = "Stop Sync"
                self.sync_button.update()
                
                print("--- Running Sync ---")
                
                self.add_list2manager()
                self.manager.start()
                
            except Exception as error:
                print(f"Error: {error}")
                e.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {error}"))
                e.page.snack_bar.open = True
                e.page.update()
            
            
        else:
            self.syncronizing = False
            self.sync_button.content = "Sync Now"
            self.sync_button.update()
            
            print("--- Stopping Sync ---")
            
            self.manager.stop()

def main(page: ft.Page):
    page.title = "Sync Resource Packs"
    comp = ResourceSync()
    page.add(comp.create_ui())

if __name__ == "__main__":
    ft.run(main)
