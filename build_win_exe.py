import json
import os
import PyInstaller.__main__
import shutil


# build the .exe
PyInstaller.__main__.run([
    'main.py',
    '--windowed'
])

# get app name and version from config.json
with open("config.json", "r") as file:  # all settings from config.json
    config_data = json.loads(file.read())  # parse it as dict
    app_name = config_data["app_name"]
    app_version = config_data["app_version"]

# copy needed files
build_path = "dist/main"  # where the .exe and its dependencies are located
os.mkdir(f"{build_path}/output", 0o777)
shutil.copy("config.json", f"{build_path}/config.json") 
shutil.copy("nothing2.ogg", f"{build_path}/nothing2.ogg")
shutil.copy("VERY_IMPORTANT_READ_ME.txt", f"{build_path}/VERY_IMPORTANT_READ_ME.txt")

# make the .zip file
zip_file_name = f"{app_name}-{app_version}-win.zip"
if os.path.exists(zip_file_name):  # delete if already exists
   os.remove(zip_file_name)
shutil.make_archive(f'{app_name}-{app_version}', "zip", build_path)

print("Binaries built with success !")
