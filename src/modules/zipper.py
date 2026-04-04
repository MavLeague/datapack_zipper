import os
import zipfile
import json

class PackZipper:
    def _write_to_zip(self, zf: zipfile.ZipFile, file_path: str, arcname: str):
        try:
            zf.write(file_path, arcname=arcname)
        except ValueError as e:
            if 'timestamps before 1980' in str(e):
                zinfo = zipfile.ZipInfo(arcname, (1980, 1, 1, 0, 0, 0))
                with open(file_path, 'rb') as f:
                    zf.writestr(zinfo, f.read())
            else:
                raise

    def add_folder_to_zip(self, zf: zipfile.ZipFile, folder_path: str, arc_folder_name: str = None, allowed_extensions: list = None):

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
                self._write_to_zip(zf, file_path, arcname)

    def verify_zip(self, zip_filename: str):
        """Prints the contents of the created zip file for verification."""
        print(f"\n--- Verifying contents of '{zip_filename}' ---")
        try:
            with zipfile.ZipFile(zip_filename, 'r') as zf:
                zf.printdir()
        except FileNotFoundError:
            print(f"Error: '{zip_filename}' not found.")
        except zipfile.BadZipFile:
            print(f"Error: '{zip_filename}' is not a valid zip file.")
            
    def get_version_folders(self, pack_path: str):
        """Extracts version folders from the pack.mcmeta file."""
        version_folders = []
        try:
            if os.path.exists(pack_path):
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

    def zip_datapack(self, root_folder: str, zip_path: str, allowed_extensions: list = None):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            self.add_folder_to_zip(zf, os.path.join(root_folder, "data"), arc_folder_name="data", allowed_extensions=allowed_extensions)
            
            # add version folders from overlays
            version_folders = self.get_version_folders(os.path.join(root_folder, "pack.mcmeta"))
            if version_folders:
                for folder in version_folders:
                    self.add_folder_to_zip(zf, os.path.join(root_folder, folder, "data"), arc_folder_name=f"{folder}/data", allowed_extensions=allowed_extensions)
            
            # write pack.mcmeta and icon
            if os.path.exists(os.path.join(root_folder, "pack.mcmeta")):
                self._write_to_zip(zf, os.path.join(root_folder, "pack.mcmeta"), "pack.mcmeta")
            if os.path.exists(os.path.join(root_folder, "pack.png")):
                self._write_to_zip(zf, os.path.join(root_folder, "pack.png"), "pack.png")

    def zip_resourcepack(self, root_folder: str, zip_path: str, allowed_extensions: list = None):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            self.add_folder_to_zip(zf, os.path.join(root_folder, "assets"), arc_folder_name="assets", allowed_extensions=allowed_extensions)
            
            # Choose which resource pack meta file to include (try both valid names)
            meta_found = False
            for candidate in ("resource_pack.mcmeta", "pack_resourcepack.mcmeta"):
                candidate_path = os.path.join(root_folder, candidate)
                if os.path.exists(candidate_path):
                    # add version folders from overlays
                    version_folders = self.get_version_folders(candidate_path)
                    if version_folders:
                        for folder in version_folders:
                            self.add_folder_to_zip(zf, os.path.join(root_folder, folder, "assets"), arc_folder_name=f"{folder}/assets", allowed_extensions=allowed_extensions)
                    
                    # write pack.mcmeta
                    self._write_to_zip(zf, candidate_path, "pack.mcmeta")
                    meta_found = True
                    break
            
            if not meta_found:
                print("No resource pack metadata file found (tried resource_pack.mcmeta, pack_resourcepack.mcmeta).")
                
            if os.path.exists(os.path.join(root_folder, "pack.png")):
                self._write_to_zip(zf, os.path.join(root_folder, "pack.png"), "pack.png")