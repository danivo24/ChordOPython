class Note:
    def __init__(self, note):
        self.note = note
        self.semitones = {
            0: "C", 1: ("C#", "Db"), 2: "D", 3: ("D#", "Eb"),
            4: "E", 5: ("F", "E#"), 6: ("F#", "Gb"), 7: "G",
            8: ("G#", "Ab"), 9: "A", 10: ("A#", "Bb"), 11: "B"
        }
        self.notes = list(self.semitones.values())
        self.notes_unpacked = [item for sublist in self.notes for item in (sublist if isinstance(sublist, tuple) else (sublist,))]

        if note not in self.notes_unpacked:
            raise ValueError(f"Invalid note: {note}")

        self.root_index = self.locate_note(note)  
        self.intervals = {}

        mapping = {
    1: 0,
    2: 2,   
    3: 4,   
    4: 5,   
    5: 7,   
    6: 9,   
    7: 11,  
    9: 14,  
    11: 17, 
    13: 21  
}
        for g, semis in mapping.items():
            idx = (self.root_index + semis) % 12
            self.intervals[g] = self.notes[idx]
    def locate_note(self, note):
        for i, n in self.semitones.items():
            if isinstance(n, tuple):
                if note in n:
                    return i
            elif note == n:
                return i