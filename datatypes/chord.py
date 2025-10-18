from datatypes.note import Note
import re, json, tempfile, wave, numpy as np
import datatypes.tools.meltysynth as ms
import easy_pil as ep
class Chord:
    def __init__(self, chord):
        self.composition = {
            "": [1, 3, 5],
            "m": [1, "b3", 5],
            "dim": [1, "b3", "b5"],
            "°": [1, "b3", "b5"],
            "aug": [1, 3, "#5"],
            "+": [1, 3, "#5"],
            "7": [1, 3, 5, "b7"],
            "maj7": [1, 3, 5, 7],
            "m7": [1, "b3", 5, "b7"],
            "ø": [1, "b3", "b5", "b7"],
            "9": [1, 3, 5, "b7", 9],
            "m9": [1, "b3", 5, "b7", 9],
            "maj9": [1, 3, 5, 7, 9],
            "11": [1, 3, 5, "b7", 9, 11],
            "13": [1, 3, 5, "b7", 9, 11, 13],
        }
        self.chord = chord
        self.parse()
        self.guitar_strings = ["E2", "A2", "D3", "G3", "B3", "E4"]
        self.settings = ms.SynthesizerSettings(44100)
        self.sound_font = ms.SoundFont.from_file("datatypes/sf2/AcousticGuitar.sf2")
        self.synth = ms.Synthesizer(self.sound_font, self.settings)
        self.set_chord_info(0)
    def note_to_midi(self, note):
        NOTE_NAMES = {
            "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
            "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
            "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
        }
        if isinstance(note, tuple):
            note = note[0]
        name = note[:-1].capitalize()
        octave = int(note[-1])
        return NOTE_NAMES[name] + (octave + 1) * 12

    def transpose_strings(self, note, semitones):
        string = note
        string_note = Note(string[0:2] if string[1] in ["#", "b"] else string[0])
        string_index = string_note.locate_note(string_note.note)
        new_index = (string_index + semitones) % 12
        new_note = string_note.semitones[new_index]
        if isinstance(new_note, tuple):
            new_note = new_note[0]
        octave = int(string[-1]) + (string_index + semitones) // 12
        return f"{new_note}{octave}"



    def generate_sound(self,
                    duration_seconds=2, velocity=100, sample_rate=44100,
                    spacing_seconds=0.07, chord_num=0):
        synth = self.synth

        frets = self.frets
        fingers = self.fingers
        barres = self.barres
        capo = self.capo

        print(frets, fingers, barres, capo)
        for frets, fingers, barres, capo in [(frets, fingers, barres, capo)]:
            new_strings = []
            finger_pos = []
            new_strings = self.guitar_strings.copy()

            for fing, (i, fret) in zip(fingers, enumerate(frets)):
                if fret.isalpha():
                    fret = ord(fret) - 86
                new_strings[i] = self.transpose_strings(new_strings[i], int(fret) - int(barres)) if fret != "x" else "C0"
                finger_pos.append(fing)
            print(new_strings)
            midi_notes = [self.note_to_midi(n) for n in new_strings]

        total_duration = spacing_seconds * (len(midi_notes) - 1) + duration_seconds
        total_samples = int(total_duration * sample_rate)
        buffer = np.zeros(total_samples, dtype=np.float32)

        for i, note in enumerate(midi_notes):
            start_sample = int(i * spacing_seconds * sample_rate)
            synth.note_on(0, note, velocity)

            note_buf = ms.create_buffer(int(duration_seconds * sample_rate))
            synth.render(note_buf, note_buf)
            synth.note_off(0, note)

            end_sample = start_sample + len(note_buf)
            buffer[start_sample:end_sample] += note_buf[:total_samples - start_sample]

        buffer /= np.max(np.abs(buffer))
        pcm16 = np.int16(buffer * 32767)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            with wave.open(tmp.name, 'wb') as wf:
                wf.setnchannels(1)       
                wf.setsampwidth(2)        
                wf.setframerate(sample_rate)
                wf.writeframes(pcm16.tobytes())
            return tmp.name
    def generate_both(self, chord_num):
        self.set_chord_info(chord_num)
        return [self.generate_sound(chord_num=chord_num), self.generate_image()]
    def get_length(self):
        note = self.root.note
        type_ = self.type.replace("/", "_").lower()
        if not type_:
            type_ = "major"
        if type_ == "m":
            type_ = "minor"
        print(self.root.note, type_)
        equivalent_json = json.load(open(f"chords_diagram/{note}/{type_}.json"))["positions"]
        self.length = len(equivalent_json)
        return self.length
    def set_chord_info(self, chord_num):
        root = self.root.note
        type = self.type.replace("/", "_").lower()
        if not type:
            type = "major"
        if type == "m":
            type = "minor"
        
        self.json = json.load(open(f"chords_diagram/{root}/{type}.json"))
        equivalent_json = self.json["positions"][chord_num]
        self.frets = equivalent_json.get("frets")
        self.fingers = equivalent_json.get("fingers")
        self.barres = equivalent_json.get("barres", 0)
        self.capo = equivalent_json.get("capo", 0)
    def generate_image(self):
        editor = ep.Editor("images/guitar.png")
        default_pos = ((4, 116))
        def move_right(p):
            if p > 5:
                p = 5
            return default_pos[0] + (p * 66) - (p * 2)
        def move_down(p):
            if p > 4:
                p = 4
            p = p - 1
            return default_pos[1] + p * 230
        frets_list = []
        for f in self.frets:
            if f.isalpha() and f != 'x':
                f = ord(f) - 86
            elif f.isalpha() and f == 'x':
                f = -1
            else:
                f = int(f)

            frets_list.append(f)
            
        fingers_list = [f if f.isdigit() else "x" for f in self.fingers]
        font = ep.Font(path=ep.Font.poppins().path, size=50)
        frets_copy = frets_list.copy()
        for i, fr in enumerate(frets_copy):
            if fr == -1:
                frets_copy.remove(fr)
        if min(min(frets_copy), 1) == 0:
            barres = ""
            barres_n = 0
        else:
            barres = str(min(frets_copy))
            barres_n = min(frets_copy)
        for i, f in enumerate(frets_list):
            if barres_n and f != -1:
                frets_list[i] = f - barres_n + 1

        editor.text((0, 50), "" if min(min(frets_copy), 1) == 0 else str(min(frets_copy)), color="black", font=font)
        pos = {}
        for i, num in enumerate(fingers_list):
            if num in pos and num != "0":
                pos[num].append(i)
            else:
                pos[num] = [i]

        intervals = {}
        for num, inds in pos.items():
            if len(inds) > 1 and num != "x":
                intervals[num] = list(range(inds[0], inds[-1]+1))
              

        for i, r in intervals.items():
            y_pos = move_down(frets_list[r[0]])
            for n in range(r[0], r[-1] + 1):
                editor.paste(ep.Editor(f"images/finger {i}.png"), (move_right(n), y_pos))
        for i in fingers_list:
            if i != "0":
                editor.paste(ep.Editor(f"images/finger {i}.png"), (move_right(int(fingers_list.index(i))), move_down(int(frets_list[fingers_list.index(i)]))))

        return editor.image
    def switch_pos_chords(self, one, two):
        old = self.json["positions"][one]
        old_ = self.json["positions"][two]
        self.json["positions"][one] = old_
        self.json["positions"][two] = old
        root = self.root.note
        type = self.type.replace("/", "_").lower()
        if not type:
            type = "major"
        if type == "m":
            type = "minor"
        json.dump(self.json, open(f"chords_diagram/{root}/{type}.json","w"))
    def parse(self):
        if len(self.chord) > 1 and self.chord[1] in ["#", "b"]:
            root_note = self.chord[:2]
            rest = self.chord[2:]
        else:
            root_note = self.chord[0]
            rest = self.chord[1:]
        
        self.root = Note(root_note)
        match = re.match(r"(.*?)(\((.*?)\))?$", rest)
        chord_type, _, alterations = match.groups()
        chord_type = chord_type.replace("8", "7")
        self.type = chord_type

        self.intervals = self.root.intervals
        self.chord_notes = []

        def get_note(degree):
            if isinstance(degree, int):
                return self.intervals[degree]
            elif isinstance(degree, str):
                alter = 0
                if degree.startswith("b"):
                    alter = -1
                    d = int(degree[1:])
                elif degree.startswith("#"):
                    alter = +1
                    d = int(degree[1:])
                else:
                    d = int(degree)
                base_note = self.intervals[d]
                base_index = self.root.locate_note(base_note if isinstance(base_note, str) else base_note[0])
                new_note = self.root.semitones[(base_index + alter) % 12]
                return new_note if isinstance(new_note, str) else new_note[0]

        formula = self.composition.get(self.type, [1, 3, 5])
        self.chord_notes = [get_note(d) for d in formula]

        if alterations:
            for alt in alterations.split("/"):
                alt = alt.strip()
                if alt.endswith("-"):
                    degree = "b" + alt[:-1]
                elif alt.endswith("+"):
                    degree = "#" + alt[:-1]
                else:
                    degree = alt
                self.chord_notes.append(get_note(degree))