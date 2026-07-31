import copy

import pytest


@pytest.fixture
def director_package():
    package = {
        "project_id": "project-fixture",
        "brief": {"canvas": "9:16", "premise": "Two characters choose to stand together."},
        "music_map": {
            "duration": 1.0,
            "bpm": 96.0,
            "sections": [
                {"id": "intro", "time": [0.0, 0.5], "music_role": "intro", "energy": 2, "emotion": "arrival"},
                {"id": "chorus", "time": [0.5, 1.0], "music_role": "chorus", "energy": 4, "emotion": "choice"},
            ],
            "cues": [{"at": 0.0, "level": 1, "source": "phrase_start"}],
        },
        "character_map": {
            "characters": [
                {"id": "A", "name": "A", "director_function": "lead the audience", "source_asset": "assets/source/A.png"},
                {"id": "B", "name": "B", "director_function": "create relationship tension", "source_asset": "assets/source/B.png"},
            ],
            "relationships": [{"pair": ["A", "B"], "dramatic_function": "allies and rivals"}],
        },
        "visual_score": {
            "project": {"duration": 1.0, "canvas": "9:16", "premise": "A and B choose together."},
            "shots": [
                {
                    "id": "S01", "time": [0.0, 0.5], "section": "intro", "energy": 2,
                    "purpose": "Introduce A and B in one world", "leverage": "completion_3s",
                    "characters": ["A", "B"], "lyric": {"text": "first", "onset": 0.0},
                    "composition": {"shot_size": "full", "arrangement": "A left, B right"},
                    "primary_action": "Both silhouettes become clearly visible",
                    "beats": [{"at": 0.0, "level": 1, "event": "reveal"}],
                    "first_frame": "Empty stage", "last_frame": "A and B face the same light",
                    "transition_out": {"type": "light_wipe", "shared_element": "warm light"},
                    "technique": "hybrid",
                    "assets": {"use": ["assets/source/A.png", "assets/source/B.png"], "missing": ["stage plate"]},
                },
                {
                    "id": "S02", "time": [0.5, 1.0], "section": "chorus", "energy": 4,
                    "purpose": "Turn the relationship into a shared choice", "leverage": "completion_rate",
                    "characters": ["A", "B"], "lyric": {"text": "second", "onset": 0.5},
                    "composition": {"shot_size": "close", "arrangement": "A and B share center"},
                    "primary_action": "The shared light closes around both characters",
                    "beats": [{"at": 0.5, "level": 1, "event": "choice"}],
                    "first_frame": "Light crosses the frame", "last_frame": "A and B hold the final composition",
                    "transition_out": {"type": "none", "shared_element": "final cover"},
                    "technique": "2.5d",
                    "assets": {"use": ["assets/source/A.png", "assets/source/B.png"], "missing": []},
                },
            ],
        },
        "animatic": {"enabled": False, "fps": 4},
    }
    return copy.deepcopy(package)
