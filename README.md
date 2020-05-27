# lr2-blender-loader
If you have a Lego Racers 2 copy, or just have its assets on your computer, you can use this set of scripts to import them on Blender to
create some cool animations or anything (be aware of copyright strikes).

## Requirements
* Blender >= 2.81
* Python >= 3.7
* [Python's Pillow](https://github.com/python-pillow/Pillow)
* The Lego Racers 2 assets [extracted with UNGTC](https://github.com/JrMasterModelBuilder/UNGTC) (you must hold a game copy then).
* [The Lego Racers 2 PNG textures pack (by Mysteli on RockRaidersUnited).](https://www.dropbox.com/s/1e82fczb67lkxrd/LEGO%20Racers%202%20Textures%20%28PNG%29.zip?dl=0)

## Usage
* Download this repository on your computer (either clone or just download the archive).
* Edit `main.py`:
```python
LR2_IMPORTER_PATH = '...'  # The abs path pointing where these scripts are.

# (...) some stuff you don't have to touch.

import_terrain(
    "...",  # The abs path of the GAMEDATA, extracted with UNGTC.
    "...",  # The abs path of the PNG textures pack.
    
    # The name of the terrain you want to import, must be one of:
    # 'SANDY BAY', 'ADVENTURE ISLAND', 'MARS', 'ARCTIC', 'XALAX/TRACK01', 'XALAX02', 'XALAX/TRACK03', 'XALAX/TRACK04', 'XALAX/TRACK05'
    "MARS"
)
```
* Open `cmd` and issue `py main.py bundle`.
* Open Blender.
* Open the `Text Editor` within Blender and create a new script with any name.
* Copy and paste the content of `main.py`.
* Press `Run Script`.

That's it! You got it!

## Gallery
