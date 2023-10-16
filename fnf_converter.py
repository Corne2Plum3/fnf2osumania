""" Module which includes classes and functions needed to convert Friday Night Funkin' charts into .osz (osu mapsets). """

from crash_window import Crash_window
import json
from math import log
import os
from pydub import AudioSegment
import traceback
import shutil
from zipfile import ZipFile

class Fnf_chart:
    """
        Object:
            Represents 1 difficulty of a song in Friday Night Funkin.
        Arguments:
            map_path (str): the path to the .JSON file map.
            song_inst_path (str): the path to the .ogg which ends by Inst
            song_voices_path (str):  the path to the .ogg which ends by Voices
            osu_object (Osu_map) : the osu mapset objects, will contains some data needed to create the file
            map_mode (1-2-3-8-9) : what notes to use.
                1 = Player 1 only ; 2 = Player 2 only ; 3 = Both players (may create 2 notes at the same time)
                8 = 8K map with Player 2 at the left and Player 1 at the right. (same than FnF)
                9 = 8K map with Player 1 at the left and Player 2 at the right. (reversed FnF)
    """
    def __init__(self, map_path, song_inst_path, song_voices_path, osu_object, map_mode):
        assert map_mode in [1,2,3,5,52,6,62,7,72,8,82,9,92,42,422]  # verify mode input
        
        self.map_path = map_path  # path to the json
        self.song_inst_path = song_inst_path
        self.song_voices_path = song_voices_path
        self.title = osu_object.title  # song title
        self.artist = osu_object.artist  # song artist
        self.map_mode = map_mode
        self.osu_object = osu_object  # the osu object (Osu_map class)
        self.offset = -osu_object.offset  # In the inputs we move audio. In reality we move the notes. (applied only at .osu files output)
        self.custom_bpm = osu_object.custom_bpm
        self.default_bpm = 120
        
    def exportOsuFile(self, path, diff_name, creator, tags):
        """
            Class method:
                Generate a .osu file.
            Arguments:
                path (str) : where to create the .osu file.
                diff_name (str) : the difficulty name to generate. (Normal, Hard, ...)
                creator (str) : map creator. In other words, the osu! username of the guy who uses this program.
                tags (str) : map tags.

            Return:
                Nothing, it's wrote on a .osu file
        """
        # function consts
        x_4K = [64,196,320,448]  # x coordinates to input in the osu file according to the column for 4K maps.
        x_5K = [51,153,256,358,460] # x coordinates for 5K map
        x_6K = [64,128,192,320,384,448] # x coordinates for 6K map
        x_7K = [36,109,182,256,329,402,475] # x coordinates for 7K map
        x_8K = [32,96,160,224,288,352,416,480]  # x coordinates for 8K map
        x_9K = [32,96,142,224,256,312,352,416,480] # x coordinates for 9K map
        audio_file_name = "audio.mp3"  # audio file name
        background_file_name = "background.jpg"  # background file name
        source = "Friday Night Funkin"
        osu_file_name = removeIllegalCharacters(f"{self.artist} - {self.title} ({creator}) [{diff_name}].osu")
        sample_set = 1  # the sampleset to use in the beatmap
        sample_index = 0  # custom sample index for hitobjects
        meter = self.osu_object.meter  # the meter to set for uninherited timing points
        volume = 50  # volume/100 of the hitsounds

        # variable settings
        # artist
        if self.artist == "" or self.artist == None:
            artist = "Unknown"
        else:
            artist = self.artist

        # amount of keys
        if self.map_mode <= 3:
            keys_count = 4
        elif self.map_mode == 5 or self.map_mode == 52:
            keys_count = 5
        elif self.map_mode == 6 or self.map_mode == 62:
            keys_count = 6
        elif self.map_mode == 7 or self.map_mode == 72:
            keys_count = 7
        elif self.map_mode == 42 or self.map_mode == 422 or self.map_mode == 8 or self.map_mode == 82:
            keys_count = 8
        elif self.map_mode == 9 or self.map_mode == 92:
            keys_count = 9

        # scroll speed
        scroll_speed = self.getScrollSpeed()

        # osu file consts
        # [General] data
        general_data = {
            "AudioFilename": audio_file_name,
            "AudioLeadIn": 0,
            "PreviewTime": -1,
            "Countdown": 0,
            "SampleSet": "None",
            "StackLeniency": 0.7,
            "Mode": 3,
            "LetterboxInBreaks": 0,
            "SpecialStyle": 0,
            "WidescreenStoryboard": 0
        }
        # [Editor] data
        editor_data = {
            "DistanceSpacing": 1,
            "BeatDivisor": 4,
            "GridSize": 32,
            "TimelineZoom": 1
        }
        # [Metadata] data
        metadata_data = {
            "Title": self.title,
            "TitleUnicode": self.title,  # (same than Title)
            "Artist": artist,
            "ArtistUnicode": artist,  # (same than Artist)
            "Creator": creator,  # (the username)
            "Version": diff_name,
            "Source": source,
            "Tags": tags,
            "BeatmapID": -1,
            "BeatmapSetID": -1
        }
        # [Difficulty] data
        difficulty_data = {
            "HPDrainRate": 5,  # HP drain
            "CircleSize": keys_count,  # amount of keys
            "OverallDifficulty": 8,  # tried to reproduce the timing in fnf (300 = 40.5ms vs 40ms in FnF)
            "ApproachRate": 6.9,  # this value is ignored in Mania
            "SliderMultiplier": scroll_speed,
            "SliderTickRate": 1
        }

        osu_file_content = "osu file format v14\n"  # we start to define the first line of the file
        
        # 1. Generate [General]/[Editor]/[Metadata]/[Difficulty]
        osu_file_content += "\n[General]\n"
        for k in general_data.keys():
            osu_file_content += f"{k}:{general_data[k]}\n"
        osu_file_content += "\n[Editor]\n"
        for k in editor_data.keys():
            osu_file_content += f"{k}:{editor_data[k]}\n"
        osu_file_content += "\n[Metadata]\n"
        for k in metadata_data.keys():
            osu_file_content += f"{k}:{metadata_data[k]}\n"
        osu_file_content += "\n[Difficulty]\n"
        for k in difficulty_data.keys():
            osu_file_content += f"{k}:{difficulty_data[k]}\n"

        # 2. Generate [Events] : define the background & breaks periods
        osu_file_content += "\n[Events]\n"

        # background
        osu_file_content += "//Background and Video events\n"
        if self.osu_object.background_path != "":  # if defined background path
            osu_file_content += f"0,0,\"{background_file_name}\",0,0\n"  # the background
        # break periods
        osu_file_content += "//Break Periods\n"
        # ignored part :p
        # storyboard (we don't care)
        osu_file_content += "//Storyboard Layer 0 (Background)\n//Storyboard Layer 1 (Fail)\n//Storyboard Layer 2 (Pass)\n//Storyboard Layer 3 (Foreground)\n//Storyboard Layer 4 (Overlay)\n//Storyboard Sound Samples"

        # 3. Generate the [TimingPoints] section
        # bpm points
        osu_file_content += "\n[TimingPoints]\n"
        timing_points = self.optimizeBPMList(self.getBPMList())  # get all points
        for i in range(len(timing_points)):
            # red tick (bpm change)
            osu_file_content += f"{int(timing_points[i][0])+self.offset},{bpmToMs(timing_points[i][1])},{meter},{sample_set},{sample_index},{volume},1,0\n"
            # green tick (scroll speed change) (to keep the same scroll speed)
            osu_file_content += f"{int(timing_points[i][0])+self.offset},{-100*(timing_points[i][1]/self.getBPM())},{meter},{sample_set},{sample_index},{volume},0,0\n"

        # 4. Generate the [HitObjects] section, where they're the notes
        osu_file_content += "\n[HitObjects]\n"

        # get the list with all notes we want (details in the function doc)
        # notes are stored in notes_list, which is a list of list with [offset, column, length]
        if self.map_mode==1:
            notes_list = self.getNotesPlayer(1)
        elif self.map_mode==2:
            notes_list = self.getNotesPlayer(2)
        elif self.map_mode==3:
            notes_list = self.getNotesPlayer(1) + self.getNotesPlayer(2)
        elif self.map_mode==5:
            notes_list = self.getNotes5K(1)
        elif self.map_mode==52:
            notes_list = self.getNotes5K(2)
        elif self.map_mode==6:
            notes_list = self.getNotes6K(1)
        elif self.map_mode==62:
            notes_list = self.getNotes6K(2)
        elif self.map_mode==7:
            notes_list = self.getNotes7K(1)
        elif self.map_mode==72:
            notes_list = self.getNotes7K(2)
        elif self.map_mode==8:
            notes_list = self.getNotes8K(1)
        elif self.map_mode==82:
            notes_list = self.getNotes8K(2)
        elif self.map_mode==9:
            notes_list = self.getNotes9K(1)
        elif self.map_mode==92:
            notes_list = self.getNotes9K(2)
        elif self.map_mode==42:
            notes_list = self.getNotesAll8K(False)
        elif self.map_mode==422:
            notes_list = self.getNotesAll8K(True)
        else:  # idk how it's possible to finish here
            notes_list = []

        notes_list.sort()  # sort the notes by offset order (using the index 0)

        # convert to osu notes
        note_type = 0  # used to determinate the 4th parameter of a hitobject. 1=normal note, 128=long note, +4=new combo
        for i in range(len(notes_list)):
            if notes_list[i][2]==0:  # normal note
                # calculate note_type
                note_type = 1  # binary: 0000 0001
                if i==0:  # first note
                    note_type += 4  # add new combo (binary: 0000 0100)
                # generate the line
                if self.map_mode == 1 or self.map_mode == 2 or self.map_mode == 3:  # 4K mode
                    osu_file_content += f"{x_4K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 5 or self.map_mode == 52: # 5K mode
                    osu_file_content += f"{x_5K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 6 or self.map_mode == 62: # 6K mode
                    osu_file_content += f"{x_6K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 7 or self.map_mode == 72: # 7K mode
                    osu_file_content += f"{x_7K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 42 or self.map_mode == 422 or self.map_mode == 8 or self.map_mode == 82:  # 8K mode
                    osu_file_content += f"{x_8K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 9 or self.map_mode == 92:  # 9K mode
                    osu_file_content += f"{x_9K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{sample_set}:0:{sample_index}:{volume}:\n"
            else:  # long/hold note
                # calculate note_type
                note_type = 128  # binary: 1000 0000
                if i==0:  # first note
                    note_type += 4  # add new combo
                # generate the line
                if self.map_mode == 1 or self.map_mode == 2 or self.map_mode == 3:  # 4K mode
                    osu_file_content += f"{x_4K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{notes_list[i][0]+notes_list[i][2]+self.offset}:{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 5 or self.map_mode == 52: # 5K mode
                    osu_file_content += f"{x_5K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{notes_list[i][0]+notes_list[i][2]+self.offset}:{sample_set}:0:{sample_index}:{volume}:\n"    
                elif self.map_mode == 6 or self.map_mode == 62: # 6K mode
                    osu_file_content += f"{x_6K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{notes_list[i][0]+notes_list[i][2]+self.offset}:{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 7 or self.map_mode == 72: # 7K mode
                    osu_file_content += f"{x_7K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{notes_list[i][0]+notes_list[i][2]+self.offset}:{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 42 or self.map_mode == 422 or self.map_mode == 8 or self.map_mode == 82:  # 8K mode
                    osu_file_content += f"{x_8K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{notes_list[i][0]+notes_list[i][2]+self.offset}:{sample_set}:0:{sample_index}:{volume}:\n"
                elif self.map_mode == 9 or self.map_mode == 92: # 9K mode
                    osu_file_content += f"{x_9K[int(notes_list[i][1])]},192,{notes_list[i][0]+self.offset},{note_type},0,{notes_list[i][0]+notes_list[i][2]+self.offset}:{sample_set}:0:{sample_index}:{volume}:\n"
        
        # 5. Create and write in the file
        with open(f"{path}/{osu_file_name}", "w", encoding="utf-8") as osu_file:
            osu_file.write(osu_file_content)

        return # nothing

    def getBPM(self):
        """
            Class method:
                Simple function which returns the BPM of the song by reading BPM property.
                If self.custom_bpm is defined, returns this value
                Note: doesn't give the offset.
            Arguments:
                None.
            Return:
                int or float: BPM of the song.
        """
        if self.custom_bpm == 0:
            json_data = json.loads(jsonRemoveExtraData(self.map_path))  # parse the file as dict
            try:  # search in "bpm" section first
                return json_data["bpm"]
            except: # search in "bpm" but into "song" section
                try:
                    return json_data["song"]["bpm"]
                except:
                    print("WARNING: Failed to find the BPM...")
        else:
            return self.custom_bpm

    def getBPMList(self):
        """
            Class method:
                Returns a list with all BPM changes.
            Arguments:
                None.
            Return:
                List of lists with 2 elements [offset, BPM_value].
        """
        bpm_list = []  # all bpm change points
        if self.custom_bpm == 0:  # if this value isn't defined
            json_data = json.loads(jsonRemoveExtraData(self.map_path))  # parse the file as dict
            for i in range(len(json_data["song"]["notes"])):
                element = json_data["song"]["notes"][i]  # this is a dict
                if "bpm" in element.keys() and element["sectionNotes"]!=[]:  # if BPM property defined and if notes exists
                        bpm_list.append([element["sectionNotes"][0][0], element["bpm"]])
            
        # if the still empty (custom bpm defined or no timing points found: we suppose there is only 1 BPM change)
        if bpm_list==[]:
            bpm_list = [[self.getNotesAll8K()[0][0], self.getBPM()]]

        return bpm_list

    def getNotesAll8K(self, swap=False):
        """
            Class method:
                Return all notes of the song.
                This is only 1 list, and the columns are as 8K: player 1 will have columns 0-3 and the player 2 column 4-7.
                The swap parameter, if true, switch the column between the player 1 and the player 2.
            Arguments:
                swap (bool=False): change the column between players 1 and 2.
            Return:
                (list) : all notes of the song
        """
        if swap:  # player 1-2
            p2_notes = self.getNotesPlayer(2)  # player 2 notes
            # player 1 + player 2
            return self.getNotesPlayer(1) + [[p2_notes[i][0],p2_notes[i][1]+4,p2_notes[i][2]] for i in range(len(p2_notes))]
        else:  # player 2-1 (like FnF)
            p1_notes = self.getNotesPlayer(1)  # player 1 notes
            # player 2 + player 1
            return self.getNotesPlayer(2) + [[p1_notes[i][0],p1_notes[i][1]+4,p1_notes[i][2]] for i in range(len(p1_notes))]

    def getNotes9K(self, player_id):
        """
            Class method:
                Return a list with all notes of 1 player.
            Arguments:
                player_id (1, or 2): player id. (1=bf ; 2=ennemy)
            Return:
                list of lists with 3 elements: [offset, column, length]
                The offset is when is the beginning of the note, in ms.
                The column says on which column is the note. 0=left1 ; 1=down1 ; 2=up1 ; 3=right1 ; 4=center ; 5=left2 ; 6=down2 ; 7=up2 ; 8=right2
                The length is how much time we have to hold the note, in ms. A simple note have 0 as length.
        """
        assert player_id==1 or player_id==2

        json_data = json.loads(jsonRemoveExtraData(self.map_path))

        notes_list = []
        for i in range(len(json_data["song"]["notes"])):
            element = json_data["song"]["notes"][i]
            right_player = (player_id==1 and element["mustHitSection"]==True) or (player_id==2 and element["mustHitSection"]==False)

            for j in range (len(element["sectionNotes"])):
                note = element["sectionNotes"][j]
                if right_player and note[1]<=8:
                    note[0] = int(note[0])  # round and apply offset
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))
                elif not(right_player) and note[1]>=9: # if there is column id over 8 => other player
                    note[0] = int(note[0])  # round offset
                    note[1] %= 9  # apply modulo 9
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))

        notes_list.sort()  # sort the notes by chronological order
        return notes_list

    def getNotes8K(self, player_id):
        """
            Class method:
                Return a list with all notes of 1 player.
            Arguments:
                player_id (1, or 2): player id. (1=bf ; 2=ennemy)
            Return:
                list of lists with 3 elements: [offset, column, length]
                The offset is when is the beginning of the note, in ms.
                The column says on which column is the note. 0=left1 ; 1=down1 ; 2=up1 ; 3=right1 ; 4=left2 ; 5=down2 ; 6=up2 ; 7=right2
                The length is how much time we have to hold the note, in ms. A simple note have 0 as length.
        """
        assert player_id==1 or player_id==2

        json_data = json.loads(jsonRemoveExtraData(self.map_path))

        notes_list = []
        for i in range(len(json_data["song"]["notes"])):
            element = json_data["song"]["notes"][i]
            right_player = (player_id==1 and element["mustHitSection"]==True) or (player_id==2 and element["mustHitSection"]==False)

            for j in range (len(element["sectionNotes"])):
                note = element["sectionNotes"][j]
                if right_player and note[1]<=7:
                    note[0] = int(note[0])  # round and apply offset
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))
                elif not(right_player) and note[1]>=8: # if there is column id over 7 => other player
                    note[0] = int(note[0])  # round offset
                    note[1] %= 8  # apply modulo 8
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))

        notes_list.sort()  # sort the notes by chronological order
        return notes_list

    def getNotes7K(self, player_id):
        """
            Class method:
                Return a list with all notes of 1 player.
            Arguments:
                player_id (1, or 2): player id. (1=bf ; 2=ennemy)
            Return:
                list of lists with 3 elements: [offset, column, length]
                The offset is when is the beginning of the note, in ms.
                The column says on which column is the note. 0=left1 ; 1=down ; 2=right1 ; 3=center ; 4=left2 ; 5=top ; 6=right2
                The length is how much time we have to hold the note, in ms. A simple note have 0 as length.
        """
        assert player_id==1 or player_id==2

        json_data = json.loads(jsonRemoveExtraData(self.map_path))

        notes_list = []
        for i in range(len(json_data["song"]["notes"])):
            element = json_data["song"]["notes"][i]
            right_player = (player_id==1 and element["mustHitSection"]==True) or (player_id==2 and element["mustHitSection"]==False)

            for j in range (len(element["sectionNotes"])):
                note = element["sectionNotes"][j]
                if right_player and note[1]<=6:
                    note[0] = int(note[0])  # round and apply offset
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))
                elif not(right_player) and note[1]>=7: # if there is column id over 6 => other player
                    note[0] = int(note[0])  # round offset
                    note[1] %= 7  # apply modulo 7
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))

        notes_list.sort()  # sort the notes by chronological order
        return notes_list

    def getNotes6K(self, player_id):
        """
            Class method:
                Return a list with all notes of 1 player.
            Arguments:
                player_id (1, or 2): player id. (1=bf ; 2=ennemy)
            Return:
                list of lists with 3 elements: [offset, column, length]
                The offset is when is the beginning of the note, in ms.
                The column says on which column is the note. 0=left1 ; 1=down ; 2=right1 ; 3=left2 ; 4=top ; 5=right2
                The length is how much time we have to hold the note, in ms. A simple note have 0 as length.
        """
        assert player_id==1 or player_id==2

        json_data = json.loads(jsonRemoveExtraData(self.map_path))

        notes_list = []
        for i in range(len(json_data["song"]["notes"])):
            element = json_data["song"]["notes"][i]
            right_player = (player_id==1 and element["mustHitSection"]==True) or (player_id==2 and element["mustHitSection"]==False)

            for j in range (len(element["sectionNotes"])):
                note = element["sectionNotes"][j]
                if right_player and note[1]<=5:
                    note[0] = int(note[0])  # round and apply offset
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))
                elif not(right_player) and note[1]>=6: # if there is column id over 5 => other player
                    note[0] = int(note[0])  # round offset
                    note[1] %= 6  # apply modulo 6
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))

        notes_list.sort()  # sort the notes by chronological order
        return notes_list

    def getNotes5K(self, player_id):
        """
            Class method:
                Return a list with all notes of 1 player.
            Arguments:
                player_id (1 or 2): player id. (1=bf ; 2=ennemy)
            Return:
                list of lists with 3 elements: [offset, column, length]
                The offset is when is the beginning of the note, in ms.
                The column says on which column is the note. 0=left ; 1=down ; 2=center ; 3=top ; 4=right
                The length is how much time we have to hold the note, in ms. A simple note have 0 as length.
        """
        assert player_id==1 or player_id==2

        json_data = json.loads(jsonRemoveExtraData(self.map_path))  # parse the file as dict

        notes_list = []  # the list we want (list of [note_start, column, note_end])
        for i in range(len(json_data["song"]["notes"])):
            element = json_data["song"]["notes"][i]
            right_player = (player_id==1 and element["mustHitSection"]==True) or (player_id==2 and element["mustHitSection"]==False)  # if the section is to the player we want

            # notes for the right player
            for j in range(len(element["sectionNotes"])):
                note = element["sectionNotes"][j]  # get the note (list of 3 elements to add)

                # clean the note to remove extra arguments that cause crashes (#19)
                # remove non-numbers arguments
                k = 0
                while k < len(note):
                    if type(note[k]) == str and not(is_a_float(note[k])):  # str which is not an number
                        del note[k]  # remove it from the list
                    else:
                        k += 1  # check the next index

                if len(note) < 3:  # if we have less than 3 arguments -> note ignored
                    pass  # do nothing
                # if there are after the cleaning, more than 3 arguments, the arguments after index 2 are ignored
                elif right_player and note[1]<=4:
                    note[0] = int(note[0])  # round and apply offset
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))
                elif not(right_player) and note[1]>=5: # if there is column id over 4 => other player
                    note[0] = int(note[0])  # round offset
                    note[1] %= 5  # apply modulo 5
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))

        notes_list.sort()  # sort the notes by chronological order
        return notes_list

    def getNotesPlayer(self, player_id):
        """
            Class method:
                Return a list with all notes of 1 player.
            Arguments:
                player_id (1 or 2): player id. (1=bf ; 2=ennemy)
            Return:
                list of lists with 3 elements: [offset, column, length]
                The offset is when is the beginning of the note, in ms.
                The column says on which column is the note. 0=left ; 1=down ; 2=top ; 3=right
                The length is how much time we have to hold the note, in ms. A simple note have 0 as length.
        """
        assert player_id==1 or player_id==2

        json_data = json.loads(jsonRemoveExtraData(self.map_path))  # parse the file as dict

        notes_list = []  # the list we want (list of [note_start_time, column, note_length])
        for i in range(len(json_data["song"]["notes"])):
            element = json_data["song"]["notes"][i]
            right_player = (player_id==1 and element["mustHitSection"]==True) or (player_id==2 and element["mustHitSection"]==False)  # if the section is to the player we want
            
            # notes for the right player
            for j in range(len(element["sectionNotes"])):
                note = element["sectionNotes"][j]  # get the note (list of 3 elements to add)

                # clean the note to remove extra arguments that cause crashes (#19)
                # remove non-numbers arguments
                k = 0
                while k < len(note):
                    if type(note[k]) == str and not(is_a_float(note[k])):  # str which is not an number
                        del note[k]  # remove it from the list
                    else:
                        if type(note[k]) == str:  # convert to float
                            note[k] = float(note[k])
                        k += 1  # check the next index

                if len(note) < 3:  # if we have less than 3 arguments -> note ignored
                    pass  # do nothing
                # if there are after the cleaning, more than 3 arguments, the arguments after index 2 are ignored
                elif right_player and note[1]<=3:
                    note[0] = int(note[0])  # round and apply offset
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))
                elif not(right_player) and note[1]>=4:  # if there is column id over 3 => other player
                    note[0] = int(note[0])  # round offset
                    note[1] %= 4  # apply modulo 4
                    note[2] = int(note[2])  # round offset
                    if note[2] < 0:
                        note[2] = 0  # if we have negative value -> simple note
                    notes_list.append(list(filter(lambda x: type(x) == int or type(x) == float, note)))       

        notes_list.sort()  # sort the notes by chronological order (using the index 0)
        return notes_list

    def getScrollSpeed(self):
        """
            Class method:
                Simple function which returns the scroll speed property defnined on the JSON file.
            Arguments:
                None.
            Return:
                float: Scroll speed value.
        """
        json_data = json.loads(jsonRemoveExtraData(self.map_path))  # parse the file as dict
        return json_data["song"]["speed"]

    def optimizeBPMList(self, bpm_list):
        """
            Class method:
                Try to remove useless BPM changes and move the 1st BPM point as early as possible.
                The BPM points are sorted by offset after this function.
            Arguments:
                bpm_list (list) : the list of all BPM points to optimize from getBPMList().
            Return:
                Optimized list of lists with 2 elements [offset, BPM_value].
        """
        if bpm_list==[]:  # if empty list
            return []
        
        bpm_list.sort()  # sort bm_list by offset
        
        # 1. Replace the BPM = 0 by the value we get using getBPM()
        # yes, you can have BPM = 0...

        if self.getBPM()>=0:
            default_bpm = self.getBPM()
        else:
            default_bpm = self.default_bpm

        for i in range(len(bpm_list)):
            if bpm_list[i][1] <= 0:
                bpm_list[i][1] = default_bpm
        
        # 2. Move the 1st BPM value
        bpm_list[0][0] -= (bpm_list[0][0]//bpmToMs(bpm_list[0][1]))*bpmToMs(bpm_list[0][1])

        # 3. Remove duplicates
        if len(bpm_list)==1:  # if BPM defined only 1 time, ignore the rest
            return bpm_list
        
        i = 0  # index of the 1st BPM point to compare (will be compared with point i+1)
        while i<len(bpm_list)-1:
            # if same BPM and point i+1 useles
            if bpm_list[i][1]==bpm_list[i+1][1]:  # if same bpm
                bpm_list.pop(i+1)
            else:
                i += 1

        return bpm_list

class Osu_map:
    """
        Object:
            Represents an osu! beatmapset
        Arguments:
            title (str) : song title.
            artist (str) : song artist.
            creator (str) : map creator. In other words, the osu! username of the guy who uses this program.
            tags (str) : map tags.
            background_path (str) : path to the background to put. Empty = no background added
            audio1_path (str) : path to audio 1 file.
        Optional arguments :
            audio2_path (str) : path to audio 2 file (useful since FnF usually uses 2 files for the song).
            audio1_volume (int 0-100) : volume in percent of the audio 1. 100% by default.
            custom_bpm (float) : if not equal to 0, will define the BPM of the whole song only 1 time.
            meter (int) : meter of the song n/4 (ex: 4 as value -> meter 4/4)
            offset (int) : move the notes by this value in ms. 0 by default.
    """

    def __init__(self, title, artist, creator, tags, audio1_path, audio2_path="", audio1_volume=100, audio2_volume=100, background_path="", custom_bpm=0, meter=4, offset=0):
        # inputs
        self.title = title  # song title
        self.artist = artist  # song artist
        self.creator = creator  # the beatmap's creator
        self.tags = tags  # the tags of the beatmap
        self.audio1_path = audio1_path  # path to the 1st ogg file
        self.audio2_path = audio2_path  # path to the 2nd ogg file
        self.audio1_volume = audio1_volume  # volume/100 of the 1st audio file
        self.audio2_volume = audio2_volume  # volume/100 of the 2nd audio file (at least 1 of them should be 100)
        self.background_path = background_path  # path to the background
        self.custom_bpm = custom_bpm  # if not null, defines the bpm. Recommanded of the bpm is the same during the whole song
        self.meter = meter  # n/4 where n is the value
        self.offset = offset  # moves the notes (in ms)

        # generated properties
        self.fnf_charts = {}  # dict of Fnf objects (1 for each difficulty) {"diff_name": Fnf_chart object}

    def addDifficulty(self, diff_name, map_mode, Fnf_chart_path):
        """
            Class method:
                 Add a difficulty to convert for the beatmapset.
                If you put a diff name that already exists, it will be replaced by the new one.
            Arguments:
                diff_name (str) : the difficulty name (osu! difficulty).
                map_mode (1-2-3-8-9) : type of map (see mode arg. from convertToOsuFile())
                Fnf_chart_path (str) : path to the fnf JSON file.
            Return:
                Nothing.
        """
        new_difficulty = Fnf_chart(Fnf_chart_path, self.audio1_path, self.audio2_path, self, map_mode)
        self.fnf_charts.update({diff_name: new_difficulty})  # add this difficulty to the list

    def removeDifficulty(self, diff_name):
        """
            Class method:
                Remove a difficulty to convert for the beatmapset.
                Do nothing if the difficulty doesn't exists.
            Arguments:
                diff_name (str) : the difficulty name (osu! difficulty) to remove.
            Return:
                Nothing.
        """
        if diff_name in self.fnf_charts.keys():  # verify if the difficulty exists
            self.fnf_charts.pop(diff_name)

class Osz_converter:
    """
        Class:
            Represents the converter itself. This class does the export.
        Arguments:
            (optional) exporting_window (Exporting_window): a window made to trace the exporting status. If undefined, the status will be displayed on the console.
    """

    def __init__(self, exporting_window=None):
        self.exporting_window = exporting_window

        # these 4 attributes are edited automatically
        self.folder_name = ""  # the name of the last folder created. Set in exportAsOsz(). (ex: "sock.clip - Ballistic")
        self.folder_path = ""  # the path to the folder created during the export. Includes the folder name. (ex: "C:/Downloads/random_folder/sock.clip - Ballistic")
        self.osz_name = ""  # the name of the last .osz created. (ex: "sock.clip - Ballistic.osz")
        self.osz_path = ""  # the path to the last .osz file created. Includes the file name. (ex: "C:/Downloads/random_folder/sock.clip - Ballistic.osz")
        
        self.__export_current_step = 0  # current step of the export
        self.__export_total_steps = 0  # total amount of steps of the export

    def deleteGeneratedFiles(self):
        """
            Class method:
                Delete (or at least try) to delete the folder and the .osz generated during the conversion.
            Arguments:
                None.
            Return:
                Nothing.
        """
        # folder
        try:
            shutil.rmtree(self.folder_path)
        except:
            print(f"WARNING: error while trying to delete the generated folder ('{self.folder_path}')")
            # idk why, but is the song title is empty, the folder will not be deleted

        # .osz
        try:
            if fileExists(self.osz_path):  # verify if the .osz exists
                os.remove(self.osz_path)
        except:
            print(f"WARNING: error while trying to delete the generated .osz ('{self.osz_path}')")

    def exportAsOsz(self, osu_map, path):
        """
            Class method:
                Export an Osu_map to a .osz.
            Arguments:
                osu_map (Osu_map object): the Osu_map to export.
            Optional arguments:
                path (str): where to create the .osz
        """
        try:
            # 0. Initialization...
            self.__export_current_step = -1
            self.__export_total_steps = 0
            self.status("Initialization...")
            self.folder_name = ""
            self.osz_name = ""
            # get total amount of steps
            self.__export_total_steps = 4 + len(osu_map.fnf_charts.keys())  # steps 1,5,6,7 + step 4
            if osu_map.audio2_path == "":  # step 2
                self.__export_total_steps += 2  # only audio 1
            else:
                self.__export_total_steps += 4  # audio 1 & 2
            if osu_map.background_path != "":
                self.__export_total_steps += 1  # includes background

            # 1. create the folder with all files to compress
            self.status("Creating the folder...")

            # artist
            if osu_map.artist == "" or osu_map.artist == None:
                artist = "Unknown"
            else:
                artist = osu_map.artist
            # define the folder name
            self.folder_name = removeIllegalCharacters(f"{artist} - {osu_map.title}")  # the folder file name
            # get the full path of the folder
            if path != "":  # if custom path defined
                self.folder_path = f"{path}/{self.folder_name}"
            else:
                self.folder_path = self.folder_name  # attribute useful if the folder has to be removed (should be set BEFORE creating the folder)
            # create the folder
            os.makedirs(self.folder_path, exist_ok=True)  # disable errors if the folder already exists

            print(self.folder_path)

            # 2. create the audio.mp3
            self.status("Importing audio file 1...")
            ogg_1 = AudioSegment.from_file(osu_map.audio1_path, format="ogg")  # create AudioSegment object from pydub library
            ogg_1 += percentTodB(osu_map.audio1_volume)  # adjust volume
            if osu_map.audio2_path == "":  # audio 1 only
                self.status("Exporting the audio as mp3...")
                ogg_1.export(f"{self.folder_path}/audio.mp3", format="mp3", bitrate="192k")  # create the audio file
            else:
                self.status("Importing audio file 2...")
                ogg_2 = AudioSegment.from_file(osu_map.audio2_path, format="ogg")  # create a 2nd AudioSegment object
                ogg_2 += percentTodB(osu_map.audio2_volume)  # adjust volume
                self.status("Merging the audios 1 and 2...")
                final_audio = ogg_1.overlay(ogg_2, position=0)  # put the 2 audios at the same time
                self.status("Exporting the audio as mp3...")
                final_audio.export(f"{self.folder_path}/audio.mp3", format="mp3", bitrate="192k") 

            # 3. create the background
            if osu_map.background_path != "":
                self.status("Importing the background...")
                shutil.copyfile(osu_map.background_path, f"{self.folder_path}/background.jpg")

            # 4. create the .OSU file
            for k in osu_map.fnf_charts.keys():
                self.status(f"Creating the .osu file for the difficulty '{k}'...")
                osu_map.fnf_charts[k].exportOsuFile(self.folder_path, k, osu_map.creator, osu_map.tags)

            # 5. compress all the folder to the .osz (fun fact: the .osz file is just a .zip)
            self.status("Compressing the generated folder to .osz file...")
            # get .osz name and path
            self.osz_name = removeIllegalCharacters(self.folder_name + ".osz")
            if path != "":
                self.osz_path = f"{path}/{self.osz_name}"
            else:
                self.osz_path = self.osz_name
            # create the .osz (basically a .zip)
            shutil.make_archive(self.folder_path, "zip", self.folder_path) # create a zip with all files created

            if os.path.isfile(self.osz_path): # checking if file exists, if it does, add a number to its name
                count = 1
                self.osz_path = self.folder_path + f" ({count}).osz"
                while os.path.isfile(self.osz_path):
                    count+= 1
                    self.osz_path = self.folder_path + f" ({count}).osz"

            os.rename(f"{self.folder_path}.zip", f"{self.osz_path}") # changing the extension file from ".zip" to ".osz" by renaming it

            # 6. remove the created folder (because now the files are in the .osz)
            self.status("Removing previously generated folder...")
            shutil.rmtree(self.folder_path)

            # 7. Done ^^
            self.status("Export done. The .osz has been created.")
            if self.exporting_window != None and self.exporting_window.window != None:
                self.exporting_window.finish(self.osz_path)  # function called for the GUI when export is complete
        
        except SystemExit:  # don't call crash window whe the window is closed
            pass
        except:
            error_window = Crash_window(traceback.format_exc())
            error_window.openWindow()

    def status(self, new_status):
        """
            Class Method:
                Called several times during exportAsOsz() to update self.stringvar_status.
            Arguments:
                new_status (str): new text to display
            Return:
                Nothing.
        """
        self.__export_current_step += 1  # update current step number (+1)

        # calculate the percentage
        if self.__export_total_steps == 0:  # unknown total steps
            percentage = 0
        else:
            percentage = int((self.__export_current_step/self.__export_total_steps) * 100)

        # view
        if self.exporting_window != None:  # if window defined to follow the status
            if self.exporting_window.window != None:  # if he's open
                self.exporting_window.changeTitle(f"Export as .osz in progress... ({percentage}%)")
                self.exporting_window.changeStatus(new_status)
            else:
                print("WARNING: Osz_converter: self.exporting_window.window is None.")
        else:
            print(f"[{percentage}%] {new_status}")

def bpmToMs(bpm):
    """
        Method:
            Convert BPM to ms, where ms is the time in milliseconds between 2 beats.
        Argument:
            bpm (int or float) : the bpm to convert.
        Return:
            (int or float) : Time between 2 beats in ms.
    """
    if bpm <= 0:
        return 0
    else:
        return 60000/bpm

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

def is_a_float(string_to_verify):
    """ 
        Method:
            Verify if a str can be converted to float. 
        Argument:
            string_to_verify (str): the str to test. 
        Return:
            (bool): returns True if the conversion is possible.
    """

    # it's just going to try to convert...
    a = 0.0  # just a random variable
    can_be_converted = False

    try:
        a = float(string_to_verify)
    except:  # failed
        can_be_converted = False
    else:  # he did it
        can_be_converted = True
    
    return can_be_converted

def is_a_int(string_to_verify):
    """ 
        Method:
            Verify if a str can be converted to int. 
        Argument:
            string_to_verify (str): the str to test. 
        Return:
            (bool): returns True if the conversion is possible.
    """

    # it's just going to try to convert...
    a = 0  # just a random variable
    can_be_converted = False

    try:
        a = int(string_to_verify)
    except:  # failed
        can_be_converted = False
    else:  # he did it
        can_be_converted = True
    
    return can_be_converted

def jsonRemoveExtraData(file_path):
    """
        Method:
            Read and remove extradata of a JSON file. Do not modify the file and returns a str.
        Argument:
            file_path (str) : path to the json file.
        Return:
            (str) : content of the json file on a str.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        # to avoid bug, we have to remove extra data
        file_data = file.readlines()

        while len(file_data) > 1:  # move all lines to the index 0
            file_data[0] += file_data.pop(1)

    if len(file_data[0]) < 2:  # the file is too short to continue...
        print("Invalid JSON file ("+file_path+"): empty or too short file.")
        return "" # the function will return nothing

    # get the beginning and the end of the interesting json part (between, {})
    # note: the file content is file_data[0]
    index_start = 0  # first '{'
    index_end = 0  # last '}'
    # get index_start
    i = 0
    while i < len(file_data[0]) and file_data[0][i] != "{":
        i += 1

    if index_start >= len(file_data[0]):  # value no found
        raise "Invalid JSON file: Character '{' no found."
    else:
        index_start = i

    # get index_end
    level = 1  # current level inside the json. The goal is to find the } which close the { at index_start
    in_str = False  # true if i is between "" (ignore the content)
    while i < len(file_data[0]):
        i += 1
        if i >= len(file_data[0]):  # i out of range
            #print(level)
            print("Invalid JSON file ("+file_path+"): missing '}'.")
            return ""
        else:
            if file_data[0][i] == '"':  # found a "
                in_str = not(in_str)  # switch between true and false
            elif file_data[0][i] == '{' and in_str == False:  # we go deeper~
                level += 1
            elif file_data[0][i] == '}' and in_str == False:
                level -= 1
                if level < 0:  # idk how it's possible
                    print("Invalid JSON file ("+file_path+"): unexcepted '}'.")
                    return ""
                elif level == 0:  # we found what we are looking for yay
                    index_end = i
                    return file_data[0][index_start:index_end+1]  # return cropped str
            # for other characters, do nothing
    
    # If nothing goes wrong the code never goes here because it always ends by a return
    return ""  # to be secure and avoid infinite loop

def percentTodB(percent):
    """ 
        Method:
            Convert a percentage (%) to decibels (dB).
        Argument:
            percent (int or float>=0): the percentage to convert.
        Return:
            (float): the dB after apply the percent.
    """
    assert percent >= 0
    if percent == 0:
        return -1e12  # to avoid -infinity
    else:
        return 10 * log(percent/100, 10)

def removeIllegalCharacters(string_to_modify):
    """ 
        Method:
            Removes unauthorized characters for file names from a string.
        Argument:
            string_to_modify (str): the str to edit.
        Return:
            (str): modified str without the annoying characters we don't want.
    """
    unauthorized_characters = ['"', '<', '>', '|', '?', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\n', '\x0b', '\x0c', '\r', '\x0e', '\x0f', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', '\x1e', '\x1f', ':', '*', '?', '\\', '/']
    result = string_to_modify

    for char in unauthorized_characters:  # invalid characters
        result = string_to_modify.replace(char, "")

    if result[-1] == "." or result[-1] == " ":  # invalid ending name
        result = result[0:-1] + "_"

    if result == "":
        result = "0"  # to have something at least...

    return result
