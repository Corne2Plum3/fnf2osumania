from fnf_converter import Fnf_chart, Osu_map, Osz_converter, jsonRemoveExtraData
from functools import partial
import json
import pathlib
import tkinter as tk
import tkinter.filedialog
import tkinter.font as tkFont
import tkinter.messagebox
import threading
from thread_with_trace import Thread_with_trace
import webbrowser

# init
with open("config.json", "r") as file:  # all settings from config.json
    config_data = json.loads(file.read())  # parse it as dict

    app_name = config_data["app_name"]
    app_version = config_data["app_version"]  # version of the application
    colors = config_data["colors"]  # dict with some colors used in the app
    delete_files_when_cancel = config_data["delete_files_when_cancel"]  # if the cancel button is pressed, delete generated files? (0 or 1)
    difficulties = config_data["init"]["difficulties"]   # the dict of lists of 2 elements {"diff_name": [map_mode (str), fnf_json_path]}
    url_github = config_data["url_github"]  # link to the application's GitHub
    url_help = config_data["url_help"]  # link to get the documentation

# widgets options lists
map_mode_values = {
    "[4K] Player 1 (Boyfriend)": 1,
    "[4K] Player 2 (opponent)": 2,
    "[4K] Players 1 and 2": 3,
    "[8K] 2 players": 8,
    "[8K] 2 players (swapped)": 9
}
map_mode_options = list(map_mode_values.keys())
meter_options = [f"{i}/4" for i in range(1, 8)]  # 1/4, 2/4, 3/4, ... 7/4
no_selected_map_mode = "(Choose an option)"  # text to display when no map mode is selected
no_selected_file_text = ""  # text to display when there isn't a file selected

class Exporting_window:
    """
        Class:
            Object which represent that window which appears during the export.
            Only 1 object of this class should be created.
        Arguments:
            master (tk.Tk): the main window of the app
    """
    def __init__(self, master):
        global map_mode_options

        # values from input
        self.master = master  # Main_window object

        # other values
        self.__is_open = False  # if the window is opened

        # widgets from openWindow() variables
        self.window = None  # the tk.Toplevel object = the window ; defined with openWindow()
        self.exporting_title_label = None
        self.exporting_status_label = None
        self.exporting_button = None
        self.exporting_title_label_var = tk.StringVar()
        self.exporting_title_label_var.set("---")
        self.exporting_status_label_var = tk.StringVar()
        self.exporting_status_label_var.set("---")
        self.exporting_button_var = tk.StringVar()
        self.exporting_button_var.set("Cancel")

    def buttonCommand(self):
        """
            Class Method:
                Called when Cancel button is pressed. Basically stop the export and closes the window.
            Arguments:
                None.
            Return:
                Nothing.
        """
        global delete_files_when_cancel
        if self.exporting_button_var.get() == "Cancel":  # if the conversion isn't finished
            self.changeTitle("Export cancelled.")
            # stop the conversion
            if self.master.osz_converter_process != None:
                self.changeStatus("Stopping export process...")
                try:
                    self.master.osz_converter_process.kill()  # kill the thread
                    self.master.osz_converter_process.join()  # definitly end it by joining the thread to the main one.
                except: 
                    print("WARNING: error when trying to end the export thread.")
            # delete created files
            if delete_files_when_cancel:
                self.changeStatus("Deleting created files...")
                self.master.osz_converter.deleteGeneratedFiles()
                # warning message
                self.changeStatus("Cancelation done.")
                tkinter.messagebox.showwarning("Export as .osz interupted", "Export as .osz canceled.\nThe generated files have been deleted")
            else:
                self.changeStatus("Cancelation done.")
                tkinter.messagebox.showwarning("Export as .osz interupted", "Export as .osz canceled.")

        # close the window anyway (also just do that if the text in the button isn't 'Cancel')
        self.closeWindow()

    def changeTitle(self, new_title):
        """ Set exporting_title_label_var and update the related label. """
        self.exporting_title_label_var.set(new_title)
        self.window.update_idletasks()  # force to update the window

    def changeStatus(self, new_status):
        """ Set exporting_status_label_var and update the related label. """
        self.exporting_status_label_var.set(new_status)
        self.window.update_idletasks()  # force to update the window

    def closeWindow(self):
        """
            Class method:
                Close the window without saving settings
            Arguments:
                None.
            Return:
                Nothing.
        """
        self.__is_open = False
        self.window.withdraw()  # method to close the window

    def finish(self, osz_path=None):
        """ 
            Class method:
                Should be called when the export is completed.
                First, change the cancel button, after shows a message (pop-up), and then closes the window.
            Arguments:
                osz_path (str): the displayed messagebox allows to show where is the generated .osz. 
            Return:
                Nothing.
        """
        global colors

        # set cancel button
        self.exporting_button_var.set("OK")  # set text
        self.exporting_button.config(bg=colors["green"])  # set button color
        self.window.title("Export complete!")
        self.window.update_idletasks()  # update the window

        # show info message
        if osz_path != None:  # if defined
            tkinter.messagebox.showinfo("Export finished.", f"The .osz file was generated succesfully!\nIt's located at '{osz_path}'.")
        else:
            tkinter.messagebox.showinfo("Export finished.", "The .osz file was generated succesfully!")
        
        # close the window
        self.closeWindow()

    def openWindow(self):
        """
            Class method:
                Initialize and open the window.
            Arguments:
                None.
            Return:
                Nothing
        """
        global colors

        if self.__is_open == False:
            self.__is_open = True

            # Create and init the window
            self.window = tk.Toplevel(self.master.window)
            self.window.title("Exporting as .osz...")
            self.window.geometry("350x100")
            self.window.resizable(width=False, height=False)  # the window can't be resized

            # widgets variables defined in __init__(), but defined here
            self.exporting_title_label_var.set("Export as .osz in progress...")
            self.exporting_status_label_var.set("Initialization...")
            self.exporting_button_var.set("Cancel")
        
            # Widgets
            frame_body = tk.Frame(self.window, padx=4, pady=4)  # used to create padding for the rest of the window
            frame_body.grid(row=0, column=0, sticky="nswe")

            # new difficulty settings part
            self.exporting_title_label = tk.Label(frame_body, anchor="nw", justify="left", textvariable=self.exporting_title_label_var, width=56)
            self.exporting_title_label.grid(row=0, column=0, columnspan=3, sticky="we")
            self.exporting_title_label.config(font=self.master.font_sans_10_b)
            self.exporting_status_label = tk.Label(frame_body, anchor="nw", justify="left", textvariable=self.exporting_status_label_var)
            self.exporting_status_label.grid(row=1, column=0, columnspan=3, sticky="we")
            self.exporting_status_label.config(font=self.master.font_sans_10)

            self.exporting_button = tk.Button(frame_body, bg=colors["red"], command=self.buttonCommand, textvariable=self.exporting_button_var)
            self.exporting_button.grid(row=2, column=1)
            self.exporting_button.config(font=self.master.font_sans_10)

            self.window.protocol("WM_DELETE_WINDOW", self.buttonCommand)  # when X button is pressed (does the same thing then the 'Cancel' button)
            self.window.mainloop()
      

class Main_window:
    """
        Class object:
            Represents the main window of the app.
            Should be created only 1 time.
            Open the window when the object is created.
        Arguments:
            None.
    """
    def __init__(self):
        self.__is_open = False  # if the window is open or not
        self.__selected_difficuly_name = ""  # name of the difficulty displayed on selected difficulty section

        # widgets from openWindow()
        self.window = tk.Tk()  # the window itself
        self.frame_body_part = None  # main layout frames
        self.frame_body_part_0 = None 
        self.frame_body_part_1 = None 
        self.difficulties_list_count_label = None  # the label widget that counts the amount of difficulties
        self.difficulties_list_listbox = None  # the listbox widget with all difficulties (created in openWindow())
        self.frame_selected_difficulty = None
        
        # fonts
        self.font_sans_10 = tkFont.Font(family="Barlow Condensed", size=10)
        self.font_sans_10_b = tkFont.Font(family="Barlow Condensed", size=10, weight="bold")
        self.font_sans_10_u = tkFont.Font(family="Barlow Condensed", size=10, underline=True)
        self.font_sans_12 = tkFont.Font(family="Barlow Condensed", size=12)

        # tkinter StringVar, DoubleVar and IntVar (values of inputs, init in self.openWindow()
        self.metadata_title_entry_var = tk.StringVar()
        self.metadata_artist_entry_var = tk.StringVar()
        self.metadata_username_entry_var = tk.StringVar()
        self.audio_1_path_entry_var = tk.StringVar()
        self.audio_2_path_entry_var = tk.StringVar()
        self.audio_1_volume_scale_var = tk.IntVar()
        self.audio_2_volume_scale_var = tk.IntVar()
        self.advanced_setting_audio_offset_spinbox_var = tk.IntVar()
        self.advanced_setting_meter_spinbox_var = tk.StringVar()
        self.advanced_setting_unique_bpm_checkbutton_var = tk.IntVar()
        self.advanced_setting_bpm_value_var = tk.DoubleVar()
        self.selected_difficulty_name_entry_var = tk.StringVar()
        self.selected_difficulty_mode_var = tk.StringVar()
        self.selected_difficulty_path_value_var = tk.StringVar()
        self.background_path_entry_var = tk.StringVar()

        # slaves windows
        self.exporting_window = Exporting_window(self)  # window which appears during exportation
        self.new_difficulty_window = New_difficulty_window(self)  # window to create a new difficulty

        # export
        self.osz_converter = Osz_converter(self.exporting_window)
        self.osz_converter_process = None  # will be Osz_converter object which does the conversion

        # open the window
        self.openWindow()  # create the window

    def addDifficultyCommand(self):
        """
            Class method:
                Function called when 'Add new difficulty' is pressed.
            Arguments:
                None.
            Return:
                Nothing.
        """
        self.new_difficulty_window.openWindow()
    
    def autoBpmCommand(self):
        """
            Class method:
                Called when 'auto' button from the advanced setting for the BPM is pressed.
            Arguments:
                None.
            Return:
                Nothing.
        """
        bpm = self.getBpmFromChart()  # (try to) get the BPM by reading a JSON file
    
        if bpm > 0:  # it would be 0 if the BPM couldn't be found
            self.advanced_setting_bpm_value_var.set(bpm)  # modify the stringvar of the bpm widget, so change the walue of the spinbox

    def closeWindow(self):
        """
            Class method:
                Close the window without saving settings
            Arguments:
                None.
            Return:
                Nothing.
        """
        self.__is_open = False
        self.window.withdraw()  # method to close the window

    def deleteDifficultyCommand(self):
        """
            Class method:
                Function called when 'Delete' from selected difficulty part is pressed.
                Delete the difficulty selected in the listbox.
            Arguments:
                None.
            Return:
                Nothing.
        """
        global difficulties

        # delete the difficulty from the dict difficulties
        old_index = self.difficulties_list_listbox.curselection()[0]  # index of the selected element in the listbox before deletion
        diff_name = self.difficulties_list_listbox.get(old_index)  # name of the diff to remove
        difficulties.pop(diff_name)

        # change the selected difficulty on the listbox
        self.difficulties_list_listbox.selection_clear(0, tk.END)  # unselect all
        if old_index >= 1:  # if there is a difficulty just above -> go on it.
            self.difficulties_list_listbox.select_set(old_index - 1)
        
        # update the widgets
        self.updateDifficultiesList()  # listbox
        self.updateSelectedDifficultyFrame()  # selected difficulty section

    def difficulties_list_listbox_callback(self, evt):
        """ 
            Class method:
                Method called when self.difficulties_list_listbox is clicked.
            Arguments:
                None. (evt is created by the callback)
            Return:
                Nothing.
        """
        self.updateSelectedDifficultyFrame()

    def exportOszCommand(self):
        """
            Class method:
                Called when 'Export .osz' button from the export section is pressed.
                Used to create the .osz.
            Arguments:
                None.
            Return:
                Nothing.
        """
        global difficulties, no_selected_file_text
        
        if self.verifyAllInputs() == True:  # verify is everything is okay

            # no constants settings

            # audio1_path, audio2_path
            if self.audio_1_path_entry_var.get()!="" and (self.audio_2_path_entry_var.get()=="" or self.audio_2_path_entry_var.get()==no_selected_file_text):  # if there is only the audio 1 used 
                audio1_path = self.audio_1_path_entry_var.get()
                audio2_path = ""
            elif self.audio_2_path_entry_var.get()!="" and (self.audio_1_path_entry_var.get()=="" or self.audio_1_path_entry_var.get()==no_selected_file_text):  # if there is only the audio 2 used
                audio1_path = self.audio_2_path_entry_var.get()
                audio2_path = ""
            else:  # 2 audios
                audio1_path = self.audio_1_path_entry_var.get()
                audio2_path = self.audio_2_path_entry_var.get()

            # background_path
            if self.background_path_entry_var.get() == no_selected_file_text:
                background_path = ""
            else:
                background_path = self.background_path_entry_var.get()

            # custom_bpm
            if self.advanced_setting_unique_bpm_checkbutton_var.get() == 1:  # if unique bpm option used
                custom_bpm = self.advanced_setting_bpm_value_var.get()
            else:
                custom_bpm = 0  # no custom bpm

            # create the Osu_map object
            mapset = Osu_map(
                self.metadata_title_entry_var.get(),  # title
                self.metadata_artist_entry_var.get(),  # artist
                self.metadata_username_entry_var.get(),  # creator
                "",  # tags
                audio1_path,  # audio 1 path
                audio2_path,  # audio 2 path
                self.audio_1_volume_scale_var.get(),  # audio volume 1
                self.audio_2_volume_scale_var.get(),  # audio volume 2
                background_path,  # background path
                custom_bpm,  # custom bpm
                int(self.advanced_setting_meter_spinbox_var.get()[0]),  # meter (send the first digit of the input)
                self.advanced_setting_audio_offset_spinbox_var.get(),  # audio offset
            )
 
            for k in difficulties.keys():  # add the difficulties
                mapset.addDifficulty(k, map_mode_values[difficulties[k][0]], difficulties[k][1])

            self.osz_converter_process = Thread_with_trace(target=self.osz_converter.exportAsOsz, args=(mapset, ""))
            # Instead of directly using a threading.Thread, we use a Thread_with_trace (a threading.Thread class found on the Internet).
            # By using traces, it adds the method .kill() to stop the thread.
            self.osz_converter_process.start()  # run it (in another thread)
            self.exporting_window.openWindow()

    def getBpmFromChart(self):
        """
            Class method:
                Read a JSON file to get the BPM. Kinda similar to Fnf_chart.getBPM().
                Display error messages if something is wrong.
            Arguments:
                json_path (str): path to the json file to read (the fnf chart).
            Return:
                (float): current BPM of the song. Returns 0 if the BPM could be found.
        """
        global difficulties

        # Verify if there is at least 1 difficulty
        if difficulties == {} or difficulties == None:
            tkinter.messagebox.showerror("Impossible to get the BPM.", "There isn't any difficulty, so impossible to get the BPM.")
            return 0

        # Get the file to check
        if self.__selected_difficuly_name == "" or self.__selected_difficuly_name == None:  # no selected difficulty
            difficulty_checked = self.difficulties_list_listbox.get(0)  # the name of the difficulty checked (first in the listbox)
        else:
            difficulty_checked = self.__selected_difficuly_name
        json_path = difficulties[difficulty_checked][1]  # give the file path
            
        # Verify if the file exists and is a json
        if fileExists(json_path) == False:
            tkinter.messagebox.showerror("Impossible to get the BPM.", f"The selected file for the '{difficulty_checked}' difficulty doesn't exists.\nChoose a JSON file for this difficulty.")
            return 0
        elif getFileExtention(json_path) != ".json":  # no json extention
                tkinter.messagebox.showerror("Impossible to get the BPM.", f"The selected file for the '{difficulty_checked}' difficulty isn't a JSON file.\nChoose a JSON file for this difficulty.")
                return 0

        # read the file get the BPM
        json_data = json.loads(jsonRemoveExtraData(json_path))  # parse the file as dict
        try:  # search in "bpm" section first
            return float(json_data["bpm"])
        except: 
            try:  # search in "bpm" but into "song" section
                return float(json_data["song"]["bpm"])
            except:  # fail
                tkinter.messagebox.showerror("Impossible to get the BPM.", f"Failed to get the BPM from the '{difficulty_checked}' difficulty.\nBe sure the file is really a FNF chart, or you can select another difficulty and try again.")
                return 0

    def openWindow(self):
        """
            Class method:
                Initialize and open the window.
            Arguments:
                None.
            Return:
                Nothing
        """
        global meter_options, difficulties, app_name, app_version, colors, config_data

        if self.__is_open == False:  # to avoid duplicates
            self.__is_open = True

            # 1. Create and init the window
            self.window.title("app_name")  # set window title
            self.window.geometry("808x538")  # set window size
            self.window.resizable(width=False, height=False)  # the window can't be resized

            # 2. Create and set the variables widgets
            # set the variables
            self.metadata_title_entry_var.set(config_data["init"]["song_title"])
            self.metadata_artist_entry_var.set(config_data["init"]["song_artist"])
            self.metadata_username_entry_var.set(config_data["init"]["username"])
            self.audio_1_path_entry_var.set(config_data["init"]["audio_1"])
            self.audio_2_path_entry_var.set(config_data["init"]["audio_2"])
            self.audio_1_volume_scale_var.set(config_data["init"]["audio_1_volume"])
            self.audio_2_volume_scale_var.set(config_data["init"]["audio_2_volume"])
            self.advanced_setting_audio_offset_spinbox_var.set(config_data["init"]["audio_offset"])
            # self.advanced_setting_meter_spinbox_var set in after the spinbox meter created (idk why he don't works here)
            self.advanced_setting_unique_bpm_checkbutton_var.set(config_data["init"]["unique_bpm"])
            self.advanced_setting_bpm_value_var.set(config_data["init"]["unique_bpm_value"])
            self.selected_difficulty_name_entry_var.set("")
            self.selected_difficulty_mode_var.set(map_mode_options[0])
            self.selected_difficulty_path_value_var.set(no_selected_file_text)
            self.background_path_entry_var.set(config_data["init"]["background"])
            
            # 3. Place widgets
            # top part
            frame_top_part = tk.Frame(self.window, bg=colors["top_background"])
            frame_top_part.grid(row=0, column=0, columnspan=2, sticky="we")

            # title
            title_label = tk.Label(frame_top_part, anchor="sw", bg=colors["top_background"], fg=colors["title"], padx=4, text=app_name)
            title_label.pack(side="left")
            title_label.config(font=self.font_sans_12)   # forced to add this everytime, else the font don't change on my linux potato
            version_label = tk.Label(frame_top_part, anchor="sw", bg=colors["top_background"], padx=4, text=app_version)
            version_label.pack(side="left")
            version_label.config(font=self.font_sans_12)

            # useful links
            github_button = tk.Button(frame_top_part, bd=0, command=partial(webbrowser.open, url_github),  fg=colors["link"], overrelief="flat", padx=4, relief="flat", text="GitHub")
            github_button.pack(side="right")
            github_button.config(font=self.font_sans_10_u)
            help_button = tk.Button(frame_top_part, bd=0, command=partial(webbrowser.open, url_help), fg=colors["link"], overrelief="flat", padx=4, relief="flat", text="Help")
            help_button.pack(side="right")
            help_button.config(font=self.font_sans_10_u)

            # body part
            self.frame_body_part = tk.Frame(self.window, name="frame_body_part", padx=4, pady=4) # all body
            self.frame_body_part.grid(row=1, column=0, sticky="nesw")
            self.frame_body_part_0 = tk.Frame(self.frame_body_part, padx=4, pady=4)  # left column
            self.frame_body_part_0.grid(row=0, column=0, sticky="nesw")
            self.frame_body_part_1 = tk.Frame(self.frame_body_part, padx=4, pady=4)  # right column
            self.frame_body_part_1.grid(row=0, column=1, sticky="nesw")

            # metadata part
            frame_metadata = tk.LabelFrame(self.frame_body_part_0, text="Metadata", padx=5, pady=5)
            frame_metadata.grid(row=0, column=0, sticky="we")
            frame_metadata.config(font=self.font_sans_10)  # forced to add this everytime, else the font don't change on my linux potato

            metadata_title_label = tk.Label(frame_metadata, anchor="nw", text="Song title")
            metadata_title_label.grid(row=0, column=0, sticky="we")
            metadata_title_label.config(font=self.font_sans_10)
            metadata_title_entry = tk.Entry(frame_metadata, textvariable=self.metadata_title_entry_var, width=51)
            metadata_title_entry.grid(row=0, column=1, sticky="we")
            metadata_title_entry.config(font=self.font_sans_10)

            metadata_artist_label = tk.Label(frame_metadata, anchor="nw", text="Song artist")
            metadata_artist_label.grid(row=1, column=0, sticky="we")
            metadata_artist_label.config(font=self.font_sans_10)
            metadata_artist_entry = tk.Entry(frame_metadata, textvariable=self.metadata_artist_entry_var, width=51)
            metadata_artist_entry.grid(row=1, column=1, sticky="we")
            metadata_artist_entry.config(font=self.font_sans_10)

            metadata_username_label = tk.Label(frame_metadata, anchor="nw", justify="left", padx=6, pady=6, text="Username")
            metadata_username_label.grid(row=2, column=0, sticky="we")
            metadata_username_label.config(font=self.font_sans_10)
            metadata_username_entry = tk.Entry(frame_metadata, textvariable=self.metadata_username_entry_var, width=22)
            metadata_username_entry.grid(row=2, column=1, sticky="w")
            metadata_username_entry.config(font=self.font_sans_10)

            # audio part
            frame_audio = tk.LabelFrame(self.frame_body_part_0, text="Audio settings", padx=5, pady=5)
            frame_audio.grid(row=1, column=0, rowspan=2, sticky="nesw")
            frame_audio.config(font=self.font_sans_10)

            audio_1_label = tk.Label(frame_audio, anchor="nw", justify="left", text="Audio file 1")
            audio_1_label.grid(row=0, column=0, columnspan=3, sticky="we")
            audio_1_label.config(font=self.font_sans_10)
            audio_1_path_entry = tk.Entry(frame_audio, textvariable=self.audio_1_path_entry_var, width=55)
            audio_1_path_entry.grid(row=1, column=0, columnspan=2, sticky="we")
            audio_1_path_entry.config(font=self.font_sans_10)
            audio_1_path_button = tk.Button(frame_audio, command=partial(setFilePath, self.audio_1_path_entry_var), padx=4, text="Set", width=4)
            audio_1_path_button.grid(row=1, column=2)
            audio_1_path_button.config(font=self.font_sans_10)

            audio_2_label = tk.Label(frame_audio, anchor="nw", justify="left", text="Audio file 2")
            audio_2_label.grid(row=2, column=0, columnspan=3, sticky="we")
            audio_2_label.config(font=self.font_sans_10)
            audio_2_path_entry = tk.Entry(frame_audio, textvariable=self.audio_2_path_entry_var, width=55)
            audio_2_path_entry.grid(row=3, column=0, columnspan=2, sticky="we")
            audio_2_path_entry.config(font=self.font_sans_10)
            audio_2_path_button = tk.Button(frame_audio, command=partial(setFilePath, self.audio_2_path_entry_var), padx=4, text="Set", width=4)
            audio_2_path_button.grid(row=3, column=2)
            audio_2_path_button.config(font=self.font_sans_10)

            audio_1_volume_scale = tk.Scale(frame_audio, from_=0, label="Volume audio 1", length=200, orient="horizontal", resolution=1, showvalue=1, tickinterval=0, to=100, variable=self.audio_1_volume_scale_var)
            audio_1_volume_scale.grid(row=4, column=0, sticky="we")
            audio_1_volume_scale.config(font=self.font_sans_10)
            audio_2_volume_scale = tk.Scale(frame_audio, from_=0, label="Volume audio 2", length=200, orient="horizontal", resolution=1, showvalue=1, tickinterval=0, to=100, variable=self.audio_2_volume_scale_var)
            audio_2_volume_scale.grid(row=5, column=0, sticky="we")
            audio_2_volume_scale.config(font=self.font_sans_10)
            audio_volume_scale_message = tk.Message(frame_audio, anchor="nw", justify="left", padx=8, pady=8, text="IMPORTANT:\nAt least 1 of the audio files should have the volume set to 100%.")
            audio_volume_scale_message.grid(row=4, column=1, rowspan=2, columnspan=2, sticky="we")
            audio_volume_scale_message.config(font=self.font_sans_10)

            # advanced settings part
            frame_advanced_settings = tk.LabelFrame(self.frame_body_part_0, text="Advanced settings", padx=5, pady=5)
            frame_advanced_settings.grid(row=3, column=0, rowspan=2, sticky="we")
            frame_advanced_settings.config(font=self.font_sans_10)

            advanced_setting_audio_offset_label = tk.Label(frame_advanced_settings, anchor="nw", justify="left", padx=4, text="Audio offset (ms)   ")
            advanced_setting_audio_offset_label.grid(row=0, column=0, sticky="we")
            advanced_setting_audio_offset_label.config(font=self.font_sans_10)
            advanced_setting_audio_offset_spinbox = tk.Spinbox(frame_advanced_settings, from_=-10000, increment=1, textvariable=self.advanced_setting_audio_offset_spinbox_var, to=10000, width=15)
            advanced_setting_audio_offset_spinbox.grid(row=0, column=1, sticky="we")
            advanced_setting_audio_offset_spinbox.config(font=self.font_sans_10)

            advanced_setting_meter_label = tk.Label(frame_advanced_settings, anchor="nw", justify="left", padx=4, text="Meter")
            advanced_setting_meter_label.grid(row=1, column=0, sticky="we")
            advanced_setting_meter_label.config(font=self.font_sans_10)
            advanced_setting_meter_spinbox = tk.Spinbox(frame_advanced_settings, textvariable=self.advanced_setting_meter_spinbox_var, values=meter_options, width=15)
            advanced_setting_meter_spinbox.grid(row=1, column=1, sticky="we")
            advanced_setting_meter_spinbox.config(font=self.font_sans_10)
            self.advanced_setting_meter_spinbox_var.set(config_data["init"]["meter"])

            advanced_setting_unique_bpm_checkbutton = tk.Checkbutton(frame_advanced_settings, anchor="w", compound="left", text="Unique BPM value", variable=self.advanced_setting_unique_bpm_checkbutton_var)
            advanced_setting_unique_bpm_checkbutton.grid(row=0, column=2, columnspan=3, sticky="we")
            advanced_setting_unique_bpm_checkbutton.config(font=self.font_sans_10)

            advanced_setting_bpm_label = tk.Label(frame_advanced_settings, anchor="ne", justify="right", padx=4, text="BPM", width=6)
            advanced_setting_bpm_label.grid(row=1, column=2, sticky="we")
            advanced_setting_bpm_label.config(font=self.font_sans_10)
            advanced_setting_bpm_value = tk.Spinbox(frame_advanced_settings, from_=10, increment=0.1, textvariable=self.advanced_setting_bpm_value_var, to=1000, width=8)
            advanced_setting_bpm_value.grid(row=1, column=3, sticky="we")
            advanced_setting_bpm_value.config(font=self.font_sans_10)
            advanced_setting_bpm_auto_button = tk.Button(frame_advanced_settings, command=self.autoBpmCommand, padx=8, text="auto")
            advanced_setting_bpm_auto_button.grid(row=1, column=4, sticky="we")
            advanced_setting_bpm_auto_button.config(font=self.font_sans_10)

            # difficulties list part
            frame_difficulties_list = tk.LabelFrame(self.frame_body_part_1, text="Difficulties", padx=5, pady=5)
            frame_difficulties_list.grid(row=0, column=0, rowspan=2, sticky="nswe")
            frame_difficulties_list.config(font=self.font_sans_10)

            self.difficulties_list_count_label = tk.Label(frame_difficulties_list, anchor="nw", justify="left", text=f"Total: --")
            self.difficulties_list_count_label.grid(row=0, column=0, columnspan=2, sticky="we")
            self.difficulties_list_count_label.config(font=self.font_sans_10)

            self.difficulties_list_listbox = tk.Listbox(frame_difficulties_list, exportselection=0, height=7, selectmode=tk.SINGLE, width=61)
            self.difficulties_list_listbox.grid(row=1, column=0, sticky="nswe")
            self.difficulties_list_listbox.config(font=self.font_sans_10)
            self.updateDifficultiesList()  # fill the listbox
            self.difficulties_list_listbox.bind('<<ListboxSelect>>', self.difficulties_list_listbox_callback)  # add callback when clicked

            difficulties_list_scrollbar = tk.Scrollbar(frame_difficulties_list, command=self.difficulties_list_listbox.yview, orient="vertical")
            difficulties_list_scrollbar.grid(row=1, column=1, sticky="ns")
            self.difficulties_list_listbox["yscrollcommand"] = difficulties_list_scrollbar.set  # link the scrollbar to the widget

            difficulties_list_add_button = tk.Button(frame_difficulties_list, bg=colors["green"], command=self.addDifficultyCommand, text="Add difficulty")
            difficulties_list_add_button.grid(row=2, column=0, columnspan=2)
            difficulties_list_add_button.config(font=self.font_sans_10)

            # selected difficulty part
            self.updateSelectedDifficultyFrame()  # function to create the whole LabelFrame + content

            # export and other part
            frame_export = tk.LabelFrame(self.frame_body_part_1, padx=5, pady=5, text="Export settings")
            frame_export.grid(row=4, column=0, sticky="nswe")
            frame_export.config(font=self.font_sans_10)

            background_label = tk.Label(frame_export, anchor="nw", justify="left", text="Background")
            background_label.grid(row=0, column=0, sticky="we")
            background_label.config(font=self.font_sans_10)
            background_path_entry = tk.Entry(frame_export, textvariable=self.background_path_entry_var, width=46)
            background_path_entry.grid(row=0, column=1, columnspan=2, sticky="we")
            background_path_entry.config(font=self.font_sans_10)
            background_path_button = tk.Button(frame_export, command=partial(setFilePath, self.background_path_entry_var), padx=4, text="Set", width=4)
            background_path_button.grid(row=0, column=3)
            background_path_button.config(font=self.font_sans_10)

            export_button = tk.Button(frame_export, bg=colors["green"], command=self.exportOszCommand, text="Export .osz")
            export_button.grid(row=2, column=0, columnspan=4)
            export_button.config(font=self.font_sans_10)

            self.window.mainloop()

    def updateDifficultiesList(self):
        """
            Class method:
                Update self.difficulties_list_listbox (the widget with the list of all difficulties).
            Arguments:
                None.
            Return:
                Nothing.
        """
        global difficulties

        # difficulties counter
        self.difficulties_list_count_label.config(text=f"Total: {len(difficulties)}")

        self.difficulties_list_listbox.delete(0, "end")  # clear listbox
        for k in difficulties.keys():  # init the listbox
            self.difficulties_list_listbox.insert("end", k)

    def updateSelectedDifficultyFrame(self):
        """
            Class method:
                Create the frame self.frame_selected_difficulty according to the selected difficulty in the listbox, and add his widgets.
                Also update self.__selected_difficuly_name
                Note: reset unsaved changes of these widgets.
            Arguments:
                None.
            Return:
                Nothing.
        """
        global difficulties, map_mode_options

        if self.frame_selected_difficulty != None:  # if the frame label difficulty already exists
            self.frame_selected_difficulty.destroy()  # remove it to create a new one (to reset)
        
        # create the frame
        self.frame_selected_difficulty = tk.LabelFrame(self.frame_body_part_1, text="Selected difficulty", padx=5, pady=5)
        self.frame_selected_difficulty.grid(row=2, column=0, rowspan=2, sticky="we")
        self.frame_selected_difficulty.config(font=self.font_sans_10)

        # create the widgets
        if self.difficulties_list_listbox.curselection() == ():  # no difficulty selected
            no_selected_dificulty_message = tk.Message(self.frame_selected_difficulty, text="No difficulty selected.\n\n\n\n\n")
            no_selected_dificulty_message.grid(row=0, column=0, columnspan=2, sticky="we")
            no_selected_dificulty_message.config(font=self.font_sans_10)

            # update the selected difficulty name
            self.__selected_difficuly_name = ""
        else:
            selected_difficulty_name_label = tk.Label(self.frame_selected_difficulty, anchor="nw", justify="left", padx=4, text="Difficulty name")
            selected_difficulty_name_label.grid(row=0, column=0, sticky="we")
            selected_difficulty_name_label.config(font=self.font_sans_10)
            selected_difficulty_name_entry = tk.Entry(self.frame_selected_difficulty, textvariable=self.selected_difficulty_name_entry_var, width=47)
            selected_difficulty_name_entry.grid(row=0, column=1, columnspan=3, sticky="we")
            selected_difficulty_name_entry.config(font=self.font_sans_10, justify="left")
            selected_difficulty_mode_label = tk.Label(self.frame_selected_difficulty, anchor="nw", justify="left", padx=4, text="Map type")
            selected_difficulty_mode_label.grid(row=1, column=0, sticky="we")
            selected_difficulty_mode_label.config(font=self.font_sans_10)
            selected_difficulty_mode_optionmenu = tk.OptionMenu(self.frame_selected_difficulty, self.selected_difficulty_mode_var, *map_mode_options)
            selected_difficulty_mode_optionmenu.grid(row=1, column=1, columnspan=3, sticky="we")
            selected_difficulty_mode_optionmenu.config(font=self.font_sans_10)

            selected_difficulty_path_label = tk.Label(self.frame_selected_difficulty, anchor="nw", justify="left", padx=4, text="JSON file")
            selected_difficulty_path_label.grid(row=2, column=0, sticky="we")
            selected_difficulty_path_label.config(font=self.font_sans_10)
            selected_difficulty_path_value = tk.Entry(self.frame_selected_difficulty, textvariable=self.selected_difficulty_path_value_var, width=47)
            selected_difficulty_path_value.grid(row=2, column=1, columnspan=3, sticky="we")
            selected_difficulty_path_value.config(font=self.font_sans_10)

            selected_difficulty_path_button = tk.Button(self.frame_selected_difficulty, command=partial(setFilePath, self.selected_difficulty_path_value_var), text="Set JSON file")
            selected_difficulty_path_button.grid(row=3, column=0)
            selected_difficulty_path_button.config(font=self.font_sans_10)
            selected_difficulty_discard_button = tk.Button(self.frame_selected_difficulty, command=self.updateSelectedDifficultyFrame, text="Discard")
            selected_difficulty_discard_button.grid(row=3, column=1, sticky="we")
            selected_difficulty_discard_button.config(font=self.font_sans_10)
            selected_difficulty_apply_button = tk.Button(self.frame_selected_difficulty, command=self.updateSelectedDifficultyValues, bg=colors["green"], text="Apply")
            selected_difficulty_apply_button.grid(row=3, column=2, sticky="we")
            selected_difficulty_apply_button.config(font=self.font_sans_10)
            selected_difficulty_delete_button = tk.Button(self.frame_selected_difficulty, command=self.deleteDifficultyCommand, bg=colors["red"], text="Delete")
            selected_difficulty_delete_button.grid(row=3, column=3, sticky="we")
            selected_difficulty_delete_button.config(font=self.font_sans_10)

            # update the values
            self.__selected_difficuly_name = self.difficulties_list_listbox.get(self.difficulties_list_listbox.curselection())  # get the diff name
            self.selected_difficulty_name_entry_var.set(self.__selected_difficuly_name)
            self.selected_difficulty_mode_var.set(difficulties[self.__selected_difficuly_name][0])
            self.selected_difficulty_path_value_var.set(difficulties[self.__selected_difficuly_name][1])

    def updateSelectedDifficultyValues(self):
        """
            Class method:
                Called when the 'Apply' button from selected difficulty section is pressed.
                Update the dictionary difficulties, or reload the whole section is an input is invalid.
            Arguments:
                None.
            Return:
                Nothing.
        """
        global difficulties
        
        # verify the the value in entry is the current difficulty name to decide what to verify
        # in both case nothing happens when the inputs are invalid
        if self.selected_difficulty_name_entry_var.get() == self.__selected_difficuly_name:  # no diff name change
            if self.verifyDifficultyInputs(self.selected_difficulty_name_entry_var, self.selected_difficulty_mode_var, self.selected_difficulty_path_value_var, [1]):
                difficulties[self.__selected_difficuly_name] = [self.selected_difficulty_mode_var.get(), self.selected_difficulty_path_value_var.get()]
        else:  # diff name change
            if self.verifyDifficultyInputs(self.selected_difficulty_name_entry_var, self.selected_difficulty_mode_var, self.selected_difficulty_path_value_var):  # valid inputs
                self.__selected_difficuly_name = self.selected_difficulty_name_entry_var.get()  # update this attribute with the new selected diff name

                # remove the old difficulty
                difficulties.pop(self.difficulties_list_listbox.get(self.difficulties_list_listbox.curselection()))  # the old name is still on the listbox
                # add the new difficulty
                difficulties.update({self.__selected_difficuly_name: [self.selected_difficulty_mode_var.get(), self.selected_difficulty_path_value_var.get()]})
                
                self.updateDifficultiesList()  # update the listbox from the main window
                self.difficulties_list_listbox.selection_clear(0, tk.END)
                self.difficulties_list_listbox.selection_set(self.difficulties_list_listbox.get(0, tk.END).index(self.__selected_difficuly_name))  # select in the listbox the selected difficulty

    def verifyAllInputs(self):
        """
            Class method:
                Verify all windows from the window and the difficulties dict if it's okay to do the export as .osz.
                Displays a error message if something is wrong.
            Arguments:
                None.
            Return:
                (bool): True if everything is fine, else False.
        """
        global difficulties, map_mode_options, meter_options

        # 1. Song data
        if self.metadata_title_entry_var.get() == "":  # if empty song title
            tkinter.messagebox.showerror("Invalid song title", "The song title isn't set.\nSet a song title.")
            return False  # quit the function
        elif len(self.metadata_title_entry_var.get()) > 127:  # too long song title
            tkinter.messagebox.showerror("Invalid song title", "The song title is way too long.\nSet a shorter song title (max. 127 characters).")
            return False
        # if the user is empty (maybe the user doesn't know?), the artist will be set to 'Unknown' by the converter
        elif len(self.metadata_artist_entry_var.get()) > 127:  # too long song artist
            tkinter.messagebox.showerror("Invalid song artist", "The song artist is way too long.\nSet a shorter song artist (max. 127 characters).")
            return False

        # 2. Audio
        # check ogg paths
        if self.audio_1_path_entry_var.get()!="":  # audio 1 only or both
            # audio 1
            if fileExists(self.audio_1_path_entry_var.get()) == False:  # audio 1 doesn't exists
                tkinter.messagebox.showerror("Invalid audio 1 file", "The selected file for the audio 1 doesn't exists.\nChoose a .ogg file.")
                return False   
            elif fileExists(self.audio_1_path_entry_var.get()) == False:  # audio 1 doesn't exists
                tkinter.messagebox.showerror("Invalid audio 1 file", "The selected file for the audio 1 doesn't exists.\nChoose a .ogg file.")
                return False
        if self.audio_2_path_entry_var.get()!="":  # audio 2 only or both
            # audio 2
            if getFileExtention(self.audio_2_path_entry_var.get()) != ".ogg":  # audio 2 isn't an ogg file
                tkinter.messagebox.showerror("Invalid audio 2 file", "The selected file for the audio 2 isn't a .ogg file.\nChoose a .ogg file.")
                return False
            elif fileExists(self.audio_2_path_entry_var.get()) == False:  # audio 2 doesn't exists
                tkinter.messagebox.showerror("Invalid audio 2 file", "The selected file for the audio 2 doesn't exists.\nChoose a .ogg file.")
                return False

        # audio volume 0% in used audios
        if self.audio_1_path_entry_var.get()!="" and self.audio_2_path_entry_var.get()=="":  # audio 1 only
            if self.audio_1_volume_scale_var.get() < 1:
                tkinter.messagebox.showerror("Invalid audio volume", "The volume of the audio 1 is 0%, so the song can't be heard.\nChoose a higher value for the audio 1.")
                return False
        elif self.audio_1_path_entry_var.get()=="" and self.audio_2_path_entry_var.get()!="":  # audio 2 only (who would do that???)
            if self.audio_1_volume_scale_var.get() < 1:
                tkinter.messagebox.showerror("Invalid audio volume", "The volume of the audio 2 is 0%, so the song can't be heard.\nChoose a higher value for the audio 2.")
                return False
        else:  # audio 1 and 2 used
            if self.audio_1_volume_scale_var.get() < 1 and self.audio_2_volume_scale_var.get() < 1:
                tkinter.messagebox.showerror("Invalid audio volume", "The volume of the audio 1 and 2 is 0%, so the song can't be heard.\nChoose a higher value for the audios.")
                return False

        # 3. Advanced settings
        if type(self.advanced_setting_audio_offset_spinbox_var.get()) != int and type(self.advanced_setting_audio_offset_spinbox_var.get()) != float:  # offset isn't a number
            tkinter.messagebox.showerror("Invalid audio offset", "The audio offset isn't a number.\nPut an integer value.")
            return False
        elif not(self.advanced_setting_meter_spinbox_var.get() in meter_options):  # invalid meter value
            tkinter.messagebox.showerror("Invalid meter", "The meter is invalid.\nChange it. The meter must be in the form 'n/4', where n is an integer between 1 and 7 included.")
            return False
        elif self.advanced_setting_unique_bpm_checkbutton_var.get() == 1 and type(self.advanced_setting_bpm_value_var.get())!=int and type(self.advanced_setting_bpm_value_var.get())!=float and self.advanced_setting_bpm_value_var.get()<=0:  # invalid bpm input (if needed)
            tkinter.messagebox.showerror("Invalid custom BPM", "The BPM of the song is invalid.\nChoose a positive number.")
            return False

        # 4. Difficulties
        if difficulties == {}:  # no difficulties
            tkinter.messagebox.showerror("No difficulty", "There isn't any difficulty to create\nUse the 'Add difficulty' button to add difficulties to convert.")
            return False
        else:
            for k in difficulties.keys():
                if not(difficulties[k][0] in map_mode_options):  # invalid map type
                    tkinter.messagebox.showerror("Invalid map type", f"The map type selected for the difficulty '{k}' isn't valid.\nSelect it from the list of difficulties and set the map type below.")
                    return False
                elif getFileExtention(difficulties[k][1]) != ".json":  # json file isn't an json file (OMEGALUL)
                    tkinter.messagebox.showerror("Invalid json file", f"The selected file for the '{k}' difficulty isn't a JSON file.\nChoose a .json file.")
                    return False
                elif fileExists(difficulties[k][1]) == False:  # json file doesn't exists
                    tkinter.messagebox.showerror("Invalid json file", f"The selected file for the '{k}' difficulty doesn't exists.\nChoose a .json file.")
                    return False

        # 5. Background
        if self.background_path_entry_var.get() != "":  # ...if defined
            if not(getFileExtention(self.background_path_entry_var.get()) in [".jpeg", ".jpg", ".png"]):  # audio 1 isn't an jpg/jpeg/png file
                tkinter.messagebox.showerror("Invalid background file", "The selected file for background isn't a supported image file.\nChoose a .jpeg/.jpg/.png file.")
                return False
            elif fileExists(self.background_path_entry_var.get()) == False:  # background file doesn't exists
                tkinter.messagebox.showerror("Invalid background file", "The selected file for the background doesn't exists.\nChoose a .jpeg/.jpg/.png file.")
                return False

        # if we reached this point everything is fine ^^
        return True

    def verifyDifficultyInputs(self, entry_var, map_mode_string_var, json_path_var, ignore_tests=[]):
        """
            Class method:
                A difficulty uses 3 inputs to be created/edited.
                Verify these inputs and displays error message for the 1st thing wrong found.
                Return True is everything is good, else if a error was found, return False.
            Arguments:
                entry_var (tk.StringVar): StringVar (value) of the name input.
                map_mode_string_var (tk.StringVar): StringVar of the map mode input.
                json_path_var (tk.StringVar): StringVar of the json file path
                (optional) ignore_test (list of int): Don't verify the elements on the lists:
                    1: difficulty name
                    2: map mode
                    3: json path
            Return:
                (bool): True if everything is OK, False if something is wrong.
        """
        global no_selected_file_text, no_selected_map_mode

        # difficulty name must not be empty and not too long (max. 127 chars), already exists diff name
        if not(1 in ignore_tests):
            if len(entry_var.get()) < 1:
                tkinter.messagebox.showerror("Invalid difficulty name", "The difficulty name is empty.\nSet the difficulty name.")
                return False # quit the function
            elif len(entry_var.get()) > 127:
                tkinter.messagebox.showerror("Invalid difficulty name", "The difficulty name is too long.\nPut a shorter difficulty name (max. 127 characters).")
                return False
            elif entry_var.get() in difficulties.keys():  # the difficulty name already exists
                tkinter.messagebox.showerror("Invalid difficulty name", "The difficulty name already exists.\nChoose another difficulty name.")
                return False

        # the map mode must not be set to "(choose a option)" (no set)
        if not(2 in ignore_tests):
            if map_mode_string_var.get() == no_selected_map_mode:
                tkinter.messagebox.showerror("Invalid map type", "The map type isn't set.\nChoose an option below 'Map type'.")
                return False

        # invalid JSON file (no file selected, the file doesn't exist, not a json)
        if not(3 in ignore_tests):
            if json_path_var.get() == no_selected_file_text:
                tkinter.messagebox.showerror("Invalid JSON path", "No file selected.\nChoose a .json file.")
                return False
            elif fileExists(json_path_var.get()) == False:
                tkinter.messagebox.showerror("Invalid JSON path", "The selected file doesn't exists.\nChoose a .json file.")
                return False
            elif getFileExtention(json_path_var.get()) != ".json":  # no json extention
                    tkinter.messagebox.showerror("Invalid JSON path", "The selected file isn't a JSON file.\nChoose a .json file.")
                    return False

        # if we are here that means the code is fine ^^
        return True

class New_difficulty_window:
    """
        Class:
            Object that represent a window which allow to create a difficulty.
            Only 1 object of this class should be created.
        Arguments:
            master (tk.Tk): the main window of the app
    """
    def __init__(self, master):
        global map_mode_options

        # values from input
        self.master = master  # Main_window object

        self.__is_open = False  # if the window is opened

        # widgets from openWindow() variables
        self.window = None  # the tk.Toplevel object = the window ; defined with openWindow()
        self.__new_difficulty_name_entry_var = tk.StringVar()
        self.__new_difficulty_name_entry_var.set("")
        self.__new_difficulty_mode_optionmenu_values = [no_selected_map_mode] + map_mode_options
        self.__new_difficulty_mode_optionmenu_var = tk.StringVar()
        self.__new_difficulty_mode_optionmenu_var.set(self.__new_difficulty_mode_optionmenu_values[0])
        self.__new_difficulty_path_value_var = tk.StringVar()
        self.__new_difficulty_path_value_var.set("")

    def closeWindow(self):
        """
            Class method:
                Close the window without saving settings
            Arguments:
                None.
            Return:
                Nothing.
        """
        self.__is_open = False
        self.window.withdraw()  # method to close the window

    def createDifficulty(self):
        """
            Class method:
                Read values of the window to create a new difficulty, then close the window.
                If an input is invalid, displays a warning/error message and does anything else.
                If a difficulty is added, update difficulties_list_listbox from the main menu.
            Arguments:
                None.
            Return:
                Nothing.
        """
        global difficulties, no_selected_file_text
        
        # Verify the inputs
        if self.master.verifyDifficultyInputs(self.__new_difficulty_name_entry_var, self.__new_difficulty_mode_optionmenu_var, self.__new_difficulty_path_value_var):  # use this method from the Main_window (return True if this is fine)
            
            # add the new difficulty
            difficulties.update({self.__new_difficulty_name_entry_var.get(): [self.__new_difficulty_mode_optionmenu_var.get(), self.__new_difficulty_path_value_var.get()]})

            self.master.updateDifficultiesList()  # update the listbox from the main window
            self.closeWindow()  # close the window

    def openWindow(self):
        """
            Class method:
                Initialize and open the window.
            Arguments:
                None.
            Return:
                Nothing
        """
        if self.__is_open == False:
            self.__is_open = True

            # Create and init the window
            self.window = tk.Toplevel(self.master.window)
            self.window.title("New difficulty")
            self.window.geometry("350x255")
            self.window.resizable(width=False, height=False)  # the window can't be resized

            # widgets variables defined in __init__()
        
            # Widgets
            frame_body = tk.Frame(self.window, padx=4, pady=4)  # used to create padding for the rest of the window
            frame_body.grid(row=0, column=0, sticky="nswe")

            # new difficulty settings part
            frame_new_difficulty = tk.LabelFrame(frame_body, text="Set the new difficulty", padx=4, pady=4)  # frame which contains all elements
            frame_new_difficulty.grid(row=0, column=0, columnspan=2, sticky="nswe")
            frame_new_difficulty.config(font=self.master.font_sans_10)

            new_difficulty_name_label = tk.Label(frame_new_difficulty, anchor="nw", justify="left", padx=4, text="Difficulty name")
            new_difficulty_name_label.grid(row=0, column=0, sticky="we")
            new_difficulty_name_label.config(font=self.master.font_sans_10)
            new_difficulty_name_entry = tk.Entry(frame_new_difficulty, textvariable=self.__new_difficulty_name_entry_var, width=54)
            new_difficulty_name_entry.grid(row=1, column=0, sticky="we")
            new_difficulty_name_entry.config(font=self.master.font_sans_10, justify="left")

            new_difficulty_mode_label = tk.Label(frame_new_difficulty, anchor="nw", justify="left", padx=4, text="Map type")
            new_difficulty_mode_label.grid(row=2, column=0, sticky="we")
            new_difficulty_mode_label.config(font=self.master.font_sans_10)
            new_difficulty_mode_optionmenu = tk.OptionMenu(frame_new_difficulty, self.__new_difficulty_mode_optionmenu_var, *self.__new_difficulty_mode_optionmenu_values)
            new_difficulty_mode_optionmenu.grid(row=3, column=0, sticky="we")
            new_difficulty_mode_optionmenu.config(font=self.master.font_sans_10)

            new_difficulty_path_label = tk.Label(frame_new_difficulty, anchor="nw", justify="left", padx=4, text="JSON file")
            new_difficulty_path_label.grid(row=4, column=0, sticky="we")
            new_difficulty_path_label.config(font=self.master.font_sans_10)
            new_difficulty_path_value = tk.Entry(frame_new_difficulty, textvariable=self.__new_difficulty_path_value_var, width=54)
            new_difficulty_path_value.grid(row=5, column=0, columnspan=3, sticky="we")
            new_difficulty_path_value.config(font=self.master.font_sans_10)
            self.__new_difficulty_path_value_var.set(no_selected_file_text)
            new_difficulty_path_button = tk.Button(frame_new_difficulty, command=partial(setFilePath, self.__new_difficulty_path_value_var), text="Set JSON file")
            new_difficulty_path_button.grid(row=6, column=0)
            new_difficulty_path_button.config(font=self.master.font_sans_10)
            
            # cancel and OK options
            new_difficulty_ok_button = tk.Button(frame_body, bg=colors["green"], command=self.createDifficulty, text="OK", width=8)
            new_difficulty_ok_button.grid(row=3, column=0)
            new_difficulty_ok_button.config(font=self.master.font_sans_10)
            new_difficulty_cancel_button = tk.Button(frame_body, bg=colors["red"], command=self.closeWindow, text="Cancel", width=8)
            new_difficulty_cancel_button.grid(row=3, column=1)
            new_difficulty_cancel_button.config(font=self.master.font_sans_10)

            self.window.mainloop()

def fileExists(file_path):
    """
        Method:
            A more secure way to know if a file exists or not.
        Arguments:
            file_path (str): path to the file to verify.
        Return:
            (bool): True if the file exists : False if the file doesn't exists.
    """
    try:
        with open(file_path):  # try to open the file
            pass
    except IOError:
        return False
    else:
        return True

def getFileExtention(file_path):
    """
        Method:
            Return the file extention of the file.
        Arguments:
            file_path (str): path to the file to get the extention
        Return:
            (str): the extention of the file in LOWERCASE. Note the extentions start by a point (e.g. '.json')
    """
    return pathlib.Path(file_path).suffix.lower()

def setFilePath(string_var):
    """
        Method:
            Open a file explorer to choose any file and write the path in a tk.StringVar object.
            If cancel is pressed do nothing.
        Argument:
            string_var (tk.StringVar): where to save the selected file path.
        Return:
            (str): value saved in the tk.StringVar.
    """
    global no_selected_file_text
    selected_file = tkinter.filedialog.askopenfilename()
    if selected_file != "" and selected_file != None:  # if a file is selected (Cancel button returns an empty str)
        string_var.set(selected_file)
    if string_var.get() == "":  # if the stringvar is empty (it can happens)
        string_var.set(no_selected_file_text)
    return selected_file

# objects
root = Main_window()  # app window
root.openWindow()

