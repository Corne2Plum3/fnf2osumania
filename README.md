# fnf2osu!mania converter

![cool_banner](https://user-images.githubusercontent.com/57914482/130650455-669ce1ab-e397-47ab-bf8e-7bd2493cecb9.jpg)

Import Friday Night Funkin charts into your osu! game.

![usage_example](https://user-images.githubusercontent.com/57914482/130650521-66264c5a-c365-4f89-a630-4cd5be4133db.JPG)

## Status
It just started, sorry for bugs (and my bad english).
If you find a bug or a question, post an [issue](https://github.com/Corne2Plum3/fnf2osumania/issues).

## Required
If you don't have this, the program will not work.
* You need [FFMPEG](https://www.ffmpeg.org/) installed on your computer, else it won't work.

### Linux additional requirements
See [Developping](https://github.com/Corne2Plum3/fnf2osumania#developping) because you will need the same requirements.

## Using it

### Windows

1. Download the `.zip` with '-win' at the end of the name.
2. Then run the `.exe` (don't delete or modify **config.json**!)

### Linux
1. Download the source code.
2. Open the terminal in the folder where there's main.py, then run:
   ```
   python3 main.py
   ```

Learn how to use it [here](https://github.com/Corne2Plum3/fnf2osumania/wiki)

## Developping
You want to looks like an hacker by doing shit with the code or improve it? Download the source code.
As a Python program, there's some requirement
* **Python 3.7** or newer. (I'm not sure with older versions of Python 3. Forget Python 2)
* These Python libraries, that can be downloaded using [pip](https://docs.python.org/fr/3.6/installing/index.html), some of them are already installed:
    * functools
    * json
    * math
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
