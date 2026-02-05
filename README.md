# Datapack Manager
This Programm is a nice assistant when creating datapacks for Minecraft. It can zip your Packs for release as well as synchronize your files directly into your minecraft instance to test it in realtime!

If you can find some mistakes, bugs or just bad programming please let me know, I'm still just a rookie:D

## Example configuration
<img width="911" height="525" alt="image" src="https://github.com/user-attachments/assets/e736445f-9d95-414f-b009-c3303b1018f3" />



## Functionality

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

### Datapack Zipper
When zipping your Datapacks, only the files and folders relevant for a datapack or resource pack are copied.
All these files will be included, except for the ```README.md``` file.
You can also place other files, such as the ```README.md``` file, in there with no impact.

### Sync Resourcepack
For this to work, you need to place your project folder into the datapacks folder in your minecraft root folder.
After selecting that root folder it detects all packs that also contain a resourcepack. When syncing it creates resourcepacks in your minecraft folder containing all the files of your project folder. These are mirrored in realtime.

#
If you have wishes or ideas don't hesitate but reach out to me with an [Issue](https://github.com/MavLeague/datapack_zipper/issues) or contribute and make a pull request! :D
