# datapack_zipper
This simple python script zips your Minecraft data- and resourcepacks!

Some parts of this code are vibe coded. If you can find some mistakes, bugs or just bad programming please let me know, I'm still just a rookie:D

## Example configuration
<img width="468" height="424" alt="image" src="https://github.com/user-attachments/assets/d907b777-3244-44c3-aba1-24413ffdf3e0" />

## Functionality
It saves the last settings in the file ```config.json``` in the same directory.
Only the files and folders relevant for a datapack or resource pack are copied.

For it to work properly, your base path should have the following structure:
```md
my_pack/
├─ 📁 data
│  └─ namespace...
├─ 📁 assets**
│  └─ namespace...
├─ 📁 <overlay-folder>*
│  ├─ 📁 data
│  │  └─ namespace...
│  └─ 📁 assets**
│     └─ namespace...
├─ 📄 pack.mcmeta
├─ 📄 resource_pack.mcmeta**
├─ 🖼️ pack.png*
└─ 📄 README.md*

*optional
**optional if no resource pack is included
```
All these files will be included, except for the ```README.md``` file.
You can also place other files, such as the ```README.md``` file, in there with no impact.

## Technical
This pack uses [Flet](https://flet.dev/) for the GUI, allowing you to easily integrate it into your own Flet UIs like this:
```bash
pip install git+https://github.com/MavLeague/datapack_zipper.git
```
```python
import flet as ft
from datapack_zipper import DatapackZipper

def main(page: ft.Page):
    page.title = "Main Application"

    # Other GUI parts could be here
    header = ft.Text("Haupt-GUI", size=24, weight=ft.FontWeight.BOLD)
    datapack_module = DatapackZipper()
    
    page.add(datapack_module.create_ui())

ft.app(target=main)
```
#
If you have wishes or ideas don't hesitate but reach out to me with an [Issue](https://github.com/MavLeague/datapack_zipper/issues) or contribute and make a pull request! :D
