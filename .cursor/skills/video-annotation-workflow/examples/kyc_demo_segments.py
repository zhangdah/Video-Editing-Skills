"""
Example SEGMENTS list from a real KYC-profile product demo.

Source video: ~4:40 screen recording at 1918x904 @ 25fps showing an AI-assisted
KYC analysis workflow. The walkthrough covers 5 parts:

    PART 1  Source of Wealth        (0:00 - 2:26)
    PART 2  Beneficial Owner        (2:26 - 2:32)
    PART 3  Risk & Negative         (2:34 - 2:55)
    PART 4  Corroboration           (2:54 - 3:52)
    PART 5  Profile Quality, Exec   (3:52 - end)
            Summary, Net Worth PDF

Drop this list into `annotate_template.py` as the SEGMENTS constant and set
W, H, FPS = 1918, 904, 25. This is a *reference* for what a realistic
multi-segment annotation config looks like; patterns to notice:

1. Mix of static boxes and dynamic interpolated boxes
2. Dynamic box with a "hold then snap" keyframe pattern around t=84.36
   (layout shift when the AI chat panel opens)
3. Very short (~1.3s) segment for a briefly-visible modal
4. Multi-keyframe box growing in place as a progress tracker populates
5. PDF panel recentering at t=272 when the UI expands the PDF view
"""

SEGMENTS = [
    # ========================================================================
    # PART 1: Source of Wealth (0:00 - 2:26)
    # ========================================================================

    # Click Chat button (top-right). Small static button highlight.
    {"start": 0.4, "end": 2.6,
     "label": "Click Chat to open AI Assistant",
     "zoom": None,
     "keyframes": [
         (0.4, (1795, 5, 1900, 38)),
         (2.5, (1795, 5, 1900, 38)),
     ]},

    # Type query in chat input at bottom-right.
    {"start": 2.8, "end": 7.4,
     "label": "Type research query to AI Assistant",
     "zoom": None,
     "keyframes": [
         (2.8, (1260, 850, 1918, 903)),
         (7.0, (1260, 850, 1918, 903)),
     ]},

    # AI response grows vertically as content streams in.
    # Good example of a box that expands over time.
    {"start": 7.6, "end": 19.5,
     "label": "AI web search -- Full corporate profile results",
     "zoom": None,
     "keyframes": [
         (7.6,  (1260, 55, 1918, 200)),
         (9.0,  (1260, 55, 1918, 260)),
         (11.0, (1260, 55, 1918, 330)),
         (12.5, (1260, 55, 1918, 500)),
         (14.0, (1260, 55, 1918, 780)),
         (16.0, (1260, 55, 1918, 870)),
         (19.2, (1260, 55, 1918, 870)),
     ]},

    # One-click apply button — static highlight.
    {"start": 19.8, "end": 22.2,
     "label": "One-click apply research to KYC draft",
     "zoom": None,
     "keyframes": [
         (19.8, (1762, 173, 1825, 200)),
         (21.5, (1762, 173, 1825, 200)),
     ]},

    # KYC profile draft generated on the left (narrow panel).
    {"start": 22.3, "end": 26.3,
     "label": "KYC profile draft generated on the left",
     "zoom": None,
     "keyframes": [
         (22.3, (5, 45, 425, 895)),
         (26.0, (5, 45, 425, 895)),
     ]},

    # Left panel expands — wider box on same y range.
    {"start": 26.4, "end": 34.0,
     "label": "Profile expands with full client details",
     "zoom": None,
     "keyframes": [
         (26.4, (5, 45, 720, 895)),
         (33.5, (5, 45, 720, 895)),
     ]},

    # Further expansion after additional client Q&A.
    {"start": 34.1, "end": 52.0,
     "label": "Supplement profile with non-public info from client",
     "zoom": None,
     "keyframes": [
         (34.1, (5, 45, 1140, 895)),
         (50.0, (5, 45, 1140, 895)),
     ]},

    # Run Check button — small target.
    {"start": 53.0, "end": 56.3,
     "label": "Click Run Check to start SOW analysis",
     "zoom": None,
     "keyframes": [
         (53.0, (960, 460, 1085, 515)),
         (56.0, (960, 460, 1085, 515)),
     ]},

    # Progress tracker modal — box grows vertically as checklist items appear.
    {"start": 56.5, "end": 66.5,
     "label": "Automated due diligence check in progress",
     "zoom": None,
     "keyframes": [
         (56.5, (605, 115, 1315, 300)),
         (58.5, (605, 115, 1315, 380)),
         (60.5, (605, 115, 1315, 500)),
         (62.5, (605, 115, 1315, 600)),
         (64.5, (605, 115, 1315, 650)),
         (66.0, (605, 115, 1315, 650)),
     ]},

    # Chronology cards — dynamic LEFT edge that moves leftward over several
    # seconds as additional cards slide in from the left.
    {"start": 66.8, "end": 76.0,
     "label": "Wealth journey chronology generated",
     "zoom": None,
     "keyframes": [
         (66.8, (945, 370, 1900, 520)),
         (67.5, (945, 370, 1900, 520)),
         (70.0, (660, 370, 1900, 520)),
         (72.5, (590, 370, 1900, 520)),
         (75.0, (520, 370, 1900, 520)),
         (75.8, (520, 370, 1900, 520)),
     ]},

    # Verification questions — ILLUSTRATES the "hold-then-snap" keyframe
    # pattern. The AI chat panel opens at t=84.36 which narrows the main
    # content area. We hold the wide box until exactly that moment, then
    # snap to the narrow layout by t=85.0 (matches the UI's transition time).
    {"start": 76.2, "end": 87.0,
     "label": "Auto-generated verification questions for each role",
     "zoom": None,
     "keyframes": [
         (76.2,  (500, 300, 1900, 870)),
         (80.0,  (500, 300, 1900, 870)),
         (84.0,  (500, 300, 1900, 870)),
         (84.36, (500, 300, 1900, 870)),    # hold
         (85.0,  (350, 320, 1240, 870)),    # snap
         (86.8,  (350, 320, 1240, 870)),
     ]},

    # Salary benchmarking research in the chat panel (vertical growth).
    {"start": 87.5, "end": 108.0,
     "label": "AI salary benchmarking research",
     "zoom": None,
     "keyframes": [
         (87.5,  (1260, 55, 1918, 250)),
         (90.0,  (1260, 55, 1918, 400)),
         (93.0,  (1260, 55, 1918, 600)),
         (96.0,  (1260, 55, 1918, 800)),
         (99.0,  (1260, 55, 1918, 870)),
         (107.5, (1260, 55, 1918, 870)),
     ]},

    {"start": 108.2, "end": 113.5,
     "label": "Apply benchmark result to profile",
     "zoom": None,
     "keyframes": [
         (108.2, (1762, 302, 1838, 325)),
         (113.0, (1762, 302, 1838, 325)),
     ]},

    {"start": 114.5, "end": 120.0,
     "label": "Click recheck to close off outstanding issue card",
     "zoom": None,
     "keyframes": [
         (114.5, (1640, 340, 1840, 380)),
         (119.5, (1640, 340, 1840, 380)),
     ]},

    # Very short (~1.5s) segment: the Resolved badge appears briefly.
    {"start": 126.5, "end": 128.0,
     "label": "Salary Benchmarking issue marked Resolved",
     "zoom": None,
     "keyframes": [
         (125.5, (500, 280, 1900, 880)),
         (126.5, (500, 280, 1900, 880)),
     ]},

    {"start": 130.0, "end": 145.5,
     "label": "Contextual plausibility gap analysis",
     "zoom": None,
     "keyframes": [
         (130.0, (500, 280, 1900, 880)),
         (145.0, (500, 280, 1900, 880)),
     ]},

    # ========================================================================
    # PART 2: Beneficial Owner (2:26 - 2:32)
    # ========================================================================

    {"start": 146.0, "end": 154.5,
     "label": "Beneficial owner identity structure analysis",
     "zoom": None,
     "keyframes": [
         (146.0, (500, 280, 1900, 540)),
         (150.0, (500, 280, 1900, 540)),
     ]},

    # ========================================================================
    # PART 3: Risk & Negative (2:34 - 2:55)
    # ========================================================================

    {"start": 160.2, "end": 172.0,
     "label": "Overall, Country, Industry & Risk Mitigation analysis",
     "zoom": None,
     "keyframes": [
         (160.2, (500, 280, 1900, 750)),
         (171.5, (500, 280, 1900, 750)),
     ]},

    # ========================================================================
    # PART 4: Corroboration (2:54 - 3:52)
    # ========================================================================

    # Very brief (~1.3s) segment: upload modal visible before file picker opens.
    # Shortening `end` is how you prevent a highlight from persisting over a
    # covering dialog.
    {"start": 177.5, "end": 178.8,
     "label": "Upload supporting documents",
     "zoom": None,
     "keyframes": [
         (177.5, (655, 95, 1265, 445)),
         (178.5, (655, 95, 1265, 445)),
     ]},

    # Large left-half slide-over (document preview).
    {"start": 185.5, "end": 195.0,
     "label": "Auto data extraction from documents",
     "zoom": None,
     "keyframes": [
         (185.5, (0, 0, 1015, 900)),
         (194.5, (0, 0, 1015, 900)),
     ]},

    {"start": 195.2, "end": 205.0,
     "label": "Corroboration -- Document data analysis",
     "zoom": None,
     "keyframes": [
         (195.2, (500, 280, 1900, 810)),
         (204.5, (500, 280, 1900, 810)),
     ]},

    {"start": 209.5, "end": 212.5,
     "label": "Upload additional document",
     "zoom": None,
     "keyframes": [
         (209.5, (655, 95, 1265, 445)),
         (212.0, (655, 95, 1265, 445)),
     ]},

    {"start": 213.0, "end": 234.0,
     "label": "Cross-document verification & discrepancies",
     "zoom": None,
     "keyframes": [
         (213.0,  (500, 280, 1900, 870)),
         (233.5,  (500, 280, 1900, 870)),
     ]},

    # ========================================================================
    # PART 5: Profile Quality + Executive / Submission / Net Worth (3:52-end)
    # ========================================================================

    {"start": 240.5, "end": 242.5,
     "label": "Scoring of profile quality",
     "zoom": None,
     "keyframes": [
         (240.5, (500, 150, 1900, 300)),
         (242.0, (500, 150, 1900, 300)),
     ]},

    # Generate dropdown button (left of Chat) — small target.
    {"start": 242.8, "end": 245.5,
     "label": "Click Generate -- Executive Summary",
     "zoom": None,
     "keyframes": [
         (242.8, (1700, 5, 1795, 40)),
         (244.0, (1700, 5, 1795, 40)),
     ]},

    {"start": 246.0, "end": 258.5,
     "label": "Auto-generated Executive Summary",
     "zoom": None,
     "keyframes": [
         (246.0, (0, 0, 1015, 900)),
         (258.0, (0, 0, 1015, 900)),
     ]},

    {"start": 259.0, "end": 269.0,
     "label": "Full Submission document -- KYC write-up",
     "zoom": None,
     "keyframes": [
         (259.0, (0, 0, 1015, 900)),
         (268.5, (0, 0, 1015, 900)),
     ]},

    # Net Worth PDF — panel recentering at t=272. Before t=271 the PDF sits
    # in the left half; after t=272 the UI expands the panel and the PDF is
    # centered. We interpolate between those two positions.
    {"start": 269.5, "end": 279.0,
     "label": "Net Worth Calculation report (PDF)",
     "zoom": None,
     "keyframes": [
         (269.5, (0, 0, 1015, 900)),
         (271.0, (0, 0, 1015, 900)),
         (272.0, (391, 0, 1514, 900)),
         (278.5, (391, 0, 1514, 900)),
     ]},
]
