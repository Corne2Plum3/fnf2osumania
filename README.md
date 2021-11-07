# fnf2osu!mania converter

![cool_banner](https://user-images.githubusercontent.com/57914482/130650455-669ce1ab-e397-47ab-bf8e-7bd2493cecb9.jpg)

Import Friday Night Funkin charts into your osu! game.

![usage_example](https://user-images.githubusercontent.com/57914482/130650521-66264c5a-c365-4f89-a630-4cd5be4133db.JPG)

## Status
Active on it.
If you find a bug or a question, post an [issue](https://github.com/Corne2Plum3/fnf2osumania/issues).

## Required
If you don't have this, the program will not work.
* You need [FFMPEG](https://www.ffmpeg.org/) installed on your computer, else it won't work. ([YouTube tutorial](https://www.youtube.com/watch?v=r1AtmY-RMyQ))
* The font called [Barlow Condensed](https://fonts.google.com/specimen/Barlow+Condensed) installed on your computer.

### Linux additional requirements
See [Developping](https://github.com/Corne2Plum3/fnf2osumania#developping) because you will need the same requirements.

## Using it
You can pick all needed files ![https://github.com/Corne2Plum3/fnf2osumania/releases](here). You should download the last version.

### Windows

1. Download `fnf2osumania-<version>-win.zip`.
2. Then unzip the file you just downloaded.
3. Finally run  `main.exe` (don't delete or modify any file!)
**Important: if you're using the .exe file, some black windows called ffmpeg.exe will spawn and dissapear after a short time. DO NOT CLOSE THEM MANUALLY, else the program will crash.**

### Linux
You have to download the source code and run it as is... Be sure you have requirements form Developping section too.
1. Download the source code.
2. Then unzip the file you just downloaded.
3. Open the terminal in the folder where there's main.py, then run this command:
   ```
   python3 main.py
   ```

Learn how to use it [here](https://github.com/Corne2Plum3/fnf2osumania/wiki).

## Developping
You want to look like an hacker by doing shit with the code, or just improve it? Download the source code.
As a Python program, there's some additional requirements
* **Python 3.7** or newer. (I'm not sure with older versions of Python 3. Forget Python 2)
* These Python libraries, that can be downloaded using [pip](https://docs.python.org/fr/3.6/installing/index.html), some of them are already installed:
    * functools
    * json
    * math
    * operator
    * os
    * pathlib
    * pydub
    * shutil
    * sys
    * tkinter *(this one can't be downloaded through pip and it's akward asf to install it. Good luck)*
    * threading
    * trace
    * webbrowser
    * zipfile
