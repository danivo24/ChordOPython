import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from just_playback import Playback
import pytubefix
import threading
import os
import shutil
import math
from PIL import Image, ImageTk as ImageTK
import chord_extractor.extractors
import librosa
from datatypes.chord import Chord
class ChordButton(tk.Button):
    def __init__(self, master, chord, time, command=None, **kwargs):
        super().__init__(master, text=chord if chord != "N" else "", command=command, **kwargs)
        self.chord = chord
        self.time = time

    def generate_image(self):
        if self.chord != "N":
            self.chord_obj = Chord(self.chord)
            self.image = self.chord_obj.generate_image()
            return self.image
        else:
            self.image = None
class ChordOPython(tk.Tk):
    def __init__(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        super().__init__()
        self.audio = AudioPlayer()
        self.dict_playback = AudioPlayer()

        self.configs = {}
        self.filename = None
        self.beat_scroll = []
        self.configs['SONGS_FOLDER'] = 'songs'
        self.configs['ALLOWED_EXTENSIONS'] = {'mp3', 'song'}
        os.makedirs(self.configs['SONGS_FOLDER'], exist_ok=True)
        self.setup_grid()

    def setup_grid(self):


        self.grid_rowconfigure(0, weight=1)
        for i in range(0, 100):
            self.grid_columnconfigure(i, weight=1)
        infobar_container = tk.Frame(self, bg="white")
        infobar_container.grid(column=0, row=2, columnspan=99, sticky="nsew")
        self.infobar = tk.Label(infobar_container, text="No song loaded! | 0:00/0:00", bg="white")
        self.infobar.pack(side="bottom", fill="both", expand=True)
        container = self.container = tk.Frame(self)
        container.grid(column=99, row=0, sticky="nsew")

        self.canvas = tk.Canvas(container)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        y_scroll = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview, width=1)
        y_scroll.grid(row=0, column=0, sticky="ns")


        self.canvas.configure(yscrollcommand=y_scroll.set)

        self.main_frame = tk.Frame(self.canvas)
        self.chord_img = tk.Label(self)
        self.chord_img.grid(row=0, column=1)

        self.main_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for i in range(0, 5):
            self.main_frame.grid_rowconfigure(i, weight=1)
        for i in range(0, 1001):
            self.main_frame.grid_columnconfigure(i, weight=1)

        def _on_mousewheel(event):
            if event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "unit")
            elif event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "unit")

                
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_mousewheel)        
        self.canvas.bind_all("<Button-5>", _on_mousewheel)        


        self._main()

    def open_file(self):
        file_path = filedialog.askopenfilename(parent=self, filetypes=[("Audio Files", "*.mp3")], title="Choose an audio file")
        if file_path and self.allowed_file(file_path):
            threading.Thread(target=lambda: self.process_audio(file_path), daemon=True).start()
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.configs['ALLOWED_EXTENSIONS']
    
    def process_audio(self, filepath, is_youtube=False):
        self.chords_images = []
        self.chords_names = []
        self.bind("<space>", lambda event: None)
        self.bind("<Left>", lambda t: None)
        self.bind("<Right>", lambda event: None)
        self.player.entryconfig("Play/Pause", state="disabled")
        pb = ProgressBar(type="indeterminate", master=self)
        self.filename = filepath
        c = self.has_chords()
        if not c:
            y, sr = librosa.load(filepath, sr=None)
            self.bpm, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            self.beat_s = librosa.frames_to_time(beat_frames, sr=sr)
            self.dur = librosa.get_duration(y=y, sr=sr)
            ce_instance = chord_extractor.extractors.Chordino(roll_on=1)
            self.chords = ce_instance.extract(filepath)
            self.save_as_file(is_youtube)
        pause = tk.Button(self, text="Play/Pause", command=self.audio.work, state="disabled")
        pause.grid(row=0, column=1,sticky="new")
        pb.kill()
        self.buttons = []
        self.audio.load_file(self.filename)
        i = 0
        beats = []
        chords = self.chords.copy()
        for i in range(math.floor(self.bpm * self.audio.duration / 60)):
            for b in chords:
                if math.floor(b[1] * self.bpm / 60) == i:
                    beats.append(math.floor(b[1] * self.bpm / 60))
        for i in range(math.floor(self.bpm * self.audio.duration / 60)):
            if i in beats:
                continue
            chords.insert(i, ["N", i * 60 / self.bpm])
        pb = ProgressBar(master=self, length=len(chords))
        for i in range(len(chords)):
            chord, time = chords[i]
            label = ChordButton(self.main_frame, chord, math.floor(time * 60 / self.bpm), borderwidth=1, relief="solid", command=lambda time=time: self.set_pos(time), bg="white", state="disabled")
            self.buttons.append(label)
            if chord not in self.chords_names and chord != "N":
                self.chords_names.append(chord)
                self.chords_images.append(label.generate_image())
                print("salvou")
            label.grid(row=i // 4, column=i % 4, sticky="nsew", padx=1, pady=1)
            pb.advance(1)
        for i in range(len(chords)):
            self.buttons[i].config(state="normal")
        pb.kill()
        
        self.bind("<space>", lambda event: self.audio.work())
        self.bind("<Left>", lambda t: self.rewind(5))
        self.bind("<Right>", lambda event: self.forward(5))
        pause.config(state="normal")
        self.player.entryconfig("Play/Pause", state="normal")
    def save_as_file(self, is_youtube=False):
        songfolder = os.path.splitext(os.path.basename(self.filename))[0]
        folder_path = os.path.join(self.configs['SONGS_FOLDER'], songfolder)
        os.makedirs(folder_path, exist_ok=True)

        with open(os.path.join(folder_path, "chords.txt"), "w", encoding="utf-8") as f:
            f.write(f"{self.bpm[0]}\n")
            for c, t in self.chords:
                f.write(f"{c} {t}\n")

        audio_ext = os.path.splitext(self.filename)[1]
        audio_copy = os.path.join(folder_path, f"{songfolder}{audio_ext}" if not songfolder.endswith(""+audio_ext) else f"{songfolder}{audio_ext}")
        if not is_youtube:
            shutil.copy2(self.filename, audio_copy)
    def has_chords(self):
        if os.path.exists(self.filename):
            songfolder = os.path.splitext(os.path.basename(self.filename))[0]
            folder_path = os.path.join(self.configs['SONGS_FOLDER'], songfolder)
            chords_file = os.path.join(folder_path, "chords.txt")
            if os.path.exists(chords_file):
                try:
                    with open(chords_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        self.bpm = float(lines[0].strip())
                        self.chords = []
                        self.beat_s = []
                        for line in lines[1:]:
                            parts = line.strip().split()
                            if len(parts) == 2:
                                chord, time = parts
                                self.chords.append((chord, float(time)))
                                self.beat_s.append(float(time))
                    return True
                except Exception as e:
                    print(f"Error reading chords file: {e}")
                    return False
    def download_youtube(self):
        url = tk.simpledialog.askstring("YouTube URL", "Enter the YouTube video URL:", parent=self)
        if url:
            threading.Thread(target=lambda: self.download_and_process(url), daemon=True).start()
    def download_and_process(self, url):
        yt = pytubefix.YouTube(url)
        stream = yt.streams.get_audio_only()
        output_path = os.path.join(self.configs['SONGS_FOLDER'], yt.title)
        if not os.path.exists(self.configs['SONGS_FOLDER']):
            os.makedirs(os.path.dir(output_path))
        file_path = stream.download(output_path=output_path, filename=yt.title+".mp3")
        threading.Thread(target=lambda: self.process_audio(file_path, True), daemon=True).start()

    def _main(self):
        self.title("ChordOPython")
        self.minsize(800, 600)
        self.toolbar = tk.Menu(self)
        self.file = tk.Menu(self.toolbar, tearoff=0)
        self.toolbar.add_cascade(label="File", menu=self.file)
        self.file.add_command(label="Open", command=self.open_file)
        self.file.add_separator()
        self.file.add_command(label="Exit", command=self.quit)

        self.player = tk.Menu(self.toolbar, tearoff=0)
        self.toolbar.add_cascade(label="Player", menu=self.player)
        self.player.add_command(label="Play/Pause", command=self.audio.work)
        
        self.tools = tk.Menu(self.toolbar, tearoff=0)
        self.toolbar.add_cascade(label="Tools", menu=self.tools)
        self.tools.add_command(label="Chord Dictionary", command=self.chord_dictionary)
        self.tools.add_command(label="Download from YouTube", command=self.download_youtube)

        self.config(menu=self.toolbar)
        self.track()
    def chord_dictionary(self):
        window = tk.Toplevel(self)
        container = tk.Frame(window)
        container.pack()

        canvas = tk.Canvas(container)
        canvas.grid(row=0, column=0, sticky="nsew")

        y_scroll = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        y_scroll.grid(row=0, column=10, sticky="nsew")


        canvas.configure(yscrollcommand=y_scroll.set)

        main_frame = tk.Frame(canvas)

        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=main_frame, anchor="nw")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for i in range(0, 5):
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(0, 1001):
            main_frame.grid_columnconfigure(i, weight=1)

        def _on_mousewheel(event):
            if event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "unit")
            elif event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "unit")
        def search():
            chord_data = []
            try:
                chord = Chord(self.tb.get("1.0", "end").strip().rstrip())
            except:
                raise ValueError("Invalid Chord!")
            finally:
                pb = ProgressBar("determinate", chord.get_length())
                for i in range(chord.get_length()):
                    chord_data.append(chord.generate_both(i))
                    pb.advance(1)
                pb.kill()
            def build(chord_data, num):
                s, i  = chord_data[num]
                self.current_chord = num
                self.dict_playback.load(s)
                play = tk.Button(canvas, text="Play", command=self.dict_playback.play)
                backward = tk.Button(canvas, text="<<", command=lambda n = self.current_chord-1: build(chord_data, n))
                forward = tk.Button(canvas, text=">>", command=lambda n = self.current_chord+1: build(chord_data, n))
                
                
                if self.current_chord == chord.get_length() - 1:
                    forward.config(state="disabled")
                else:
                    forward.config(state="normal")
                if self.current_chord == 0:
                    backward.config(state="disabled")
                else:
                    backward.config(state="normal")
                image = ImageTK.PhotoImage(i.resize((200, 500), Image.Resampling.LANCZOS))
                label = tk.Label(canvas, image=image)
                label.grid(row=3, column=2)
                label.image = image
                play.grid(row=4, column=2)
                backward.grid(row=4, column=1)
                forward.grid(row=4, column=3)
                set_default = tk.Button(canvas, text="Set as default shape", command=lambda ch=self.current_chord: chord.switch_pos_chords(0, ch))
                set_default.grid(row=5, column=3)
            build(chord_data, self.current_chord)


                    
                
        self.current_chord = 0
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)        
        canvas.bind_all("<Button-5>", _on_mousewheel)

        self.tb_info = tk.Label(canvas, text="Type the name of a chord:")
        self.tb = tk.Text(canvas, height=1)
        self.tb_confirm = tk.Button(main_frame, text="Search", command = lambda: threading.Thread(target=search).start())
        self.tb_info.grid(row=0, column=0)
        self.tb.grid(row=1, column=0, ipady=1)
        self.tb_confirm.grid(row=2, column=0)


        
    def track(self):
        if self.audio.active and self.audio.playing:
            pos = math.floor(self.audio.curr_pos * self.bpm / 60)
            self.buttons[pos].config(bg="lightblue") if pos < len(self.buttons) else None
            self.buttons[pos - 1].config(bg="white") if pos - 1 < len(self.buttons) and pos - 1 >= 0 else None
            if pos + 2 <= len(self.buttons):
                for i in range(0, 3):
                    if self.buttons[pos + i].chord and self.buttons[pos + i].chord != "N":
                        
                        image = ImageTK.PhotoImage(self.chords_images[self.chords_names.index(self.buttons[pos + i].chord)].resize((200, 500), Image.Resampling.LANCZOS))
                        self.chord_img.config(image=image)
                        self.chord_img.image = image
                        break
            if math.floor(self.bpm/60 * self.audio.curr_pos) % 12 == 0 and math.floor(self.bpm / 60 * self.audio.curr_pos) not in self.beat_scroll and math.floor(self.bpm / 60 * self.audio.curr_pos) != 0:
                try:
                    self.canvas.yview_scroll(1, "unit")
                    self.beat_scroll.append(math.floor(self.bpm / 60 * self.audio.curr_pos))
                except:
                    pass
            
        if self.filename:
            startstop = "\u25B6" if self.audio.playing else "\u23F8"
            self.infobar.config(
    text=f"{startstop} | "
         f"{math.floor(self.audio.curr_pos) // 60:02}:{math.floor(self.audio.curr_pos) % 60:02}/"
         f"{math.floor(self.audio.duration) // 60:02}:{math.floor(self.audio.duration) % 60:02} | "
         f"{os.path.split(self.filename)[1]}"

)
        self.after(50, self.track)
    def set_pos(self, pos):
        if not self.audio.active:
            self.audio.play()
        self.beat_scroll = []
        for b in self.buttons:
            b.config(bg="white")
        self.audio.seek(pos)
    def rewind(self, seconds=5):
        for b in self.buttons:
            b.config(bg="white")
        new_pos = max(0, self.audio.curr_pos - seconds)
        self.audio.seek(new_pos)
    def forward(self, seconds=5):
        for b in self.buttons:
            b.config(bg="white")
        new_pos = min(self.audio.duration, self.audio.curr_pos + seconds)
        self.audio.seek(new_pos)



class AudioPlayer(Playback):
    def __init__(self):
        super().__init__()
    def load(self, file):
        self.filepath = file
        self.load_file(file)
    def work(self):
        if not self.active:
            self.play()
        elif self.active and self.playing:
            self.pause()
        else:
            self.resume()
    def rewind(self, seconds=5):
        new_pos = max(0, self.curr_pos - seconds)
        self.seek(new_pos)
    def forward(self, seconds=5):
        new_pos = min(self.duration, self.curr_pos + seconds)
        self.seek(new_pos)
class ProgressBar(tk.Toplevel):
    def __init__(self, type="determinate", length=1, **kwargs):
        super().__init__(**kwargs)
        self.geometry("200x25")
        self.minsize(200, 50)
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.resizable(False, False)
        self.type = type
        self.title("Processing...")
        self.length = length
        self.progress = ttk.Progressbar(self, mode=type, length=200, maximum=length)
        self.progress.pack()
        if self.type == "determinate":
            self.progress["value"] = 0
            self.progress_text = tk.Label(self, text=f"0/{length}")
            self.progress_text.pack(pady=1)
    def kill(self):
        self.destroy()
    def advance(self, n):
        if self.type == "determinate":
            self.progress["value"] += n
            self.update_idletasks()
            self.progress_text.configure(text=f"{self.progress['value']}/{self.length}")

            


app = ChordOPython()
app.mainloop()
