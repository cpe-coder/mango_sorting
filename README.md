# Mango_sorting

- Identify the mango either small, medium and large using weight sensor.
- Classify the maturity of mango either ripe or raw.
- Automation for sorting mango with separate basket for each size and maturity

### To run this python code easily using batch file

- Open project folder in terminal and paste this command then hit enter, to add virtual environment in your project folder.

```Ruby
   python -m venv venv
```

#

- Activate virtual environment using this command.
- Add activate.bat file inside the project folder where python script or .py file is located.
- Paste and save this script.

```Ruby
   REM Activate the virtual environment
   call "%~dp0venv\Scripts\activate.bat"

   REM Install required packages
   pip install opencv-python
   pip install firebase_admin

   REM Deactivate the virtual environment
   deactivate
```

- Run this script to install required packages.
- This file is located to your project folder and double click to activate.
- After installing all the required package this automatically close.

#

- Now, to run python file ex.(python.py).
- Open new text file and paste this script, save the file on desktop and name the file of
  ex.(detection.cmd or detection.bat).

```ruby
   @echo off
   REM Change to the directory where the Python script is located
   cd /d "path where your .py code is indicated"

   REM Activate virtual environment
   call "path\venv\Scripts\activate.bat"

   REM Run the Python script
   python file.py

   pause

```

- After saving, Double click the file to run the script.
