clips = [
    "00: Griffith city panorama",
    "01: Evening palm street driving",
    "02: Highway driving POV",
    "03: Beverly Hills palm road",
    "04: Coastal highway palms",
    "05: Hillside town driving",
    "06: Arms spread intersection",
    "07: Cactus street walk",
    "08: Theater facade",
    "09: Street couple selfie",
    "10: Beach couple selfie",
    "11: Boardwalk selfie",
    "12: Palm tree couple",
    "13: Looking at beach",
    "14: Small town ice cream street",
    "15: Beach plaza ocean view",
    "16: Waikiki Diamond Head",
    "17: Waikiki beach crowd",
    "18: Koolau mountains palms",
    "19: Tropical rainforest green",
    "20: Mountain McDonalds view",
    "21: Honolulu street male",
    "22: Eating snack male",
    "23: Driving in Hawaii male",
    "24: Beach couple selfie HI",
    "25: Kalakaua Ave peace sign",
    "26: Laughing together palms",
    "27: Sunset beach couple",
    "29: Sunset ending (0044+0045)",
]

intro_dur = 3.0
clip_dur = 2.986
t = intro_dur
for c in clips:
    print(f"  {int(t//60)}:{t%60:04.1f} - {int((t+clip_dur)//60)}:{(t+clip_dur)%60:04.1f}  {c}")
    t += clip_dur
