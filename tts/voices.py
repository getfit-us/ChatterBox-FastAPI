import json
import os
from typing import TypedDict


class Voice(TypedDict):
    name: str
    path: str
    exaggeration: float
    cfg_weight: float


def get_voices():
    """returns all the current custom voices. If no voices are found, it creates a new file and returns an empty list."""
    voices: list[Voice] = []
    try:
        if os.path.exists("config/voices.json"):
            with open("config/voices.json", "r") as f:
                voices = json.load(f)
        else:
            os.makedirs("config", exist_ok=True)
            voices = []
            with open("config/voices.json", "w") as f:
                json.dump(voices, f)
    except Exception as e:
        print(f"Error getting voices: {e}")
        return voices

  

    return voices


def get_voice_by_name(name: str):
    """returns a voice object by name"""
    try:
        voices = get_voices()
        return next((voice for voice in voices if voice["name"] == name), None)
    except Exception as e:
        print(f"Error getting voice by name: {e}")
        return None
    
    
def add_voice(voice: Voice):
    """adds a voice to the voices.json file"""
    voices = get_voices()
    voices.append(voice)
    with open("config/voices.json", "w") as f:
        json.dump(voices, f)
    return voices

def delete_voice(name: str):
    """deletes a voice from the voices.json file"""
    voices = get_voices()
    voices = [voice for voice in voices if voice["name"] != name]
    with open("config/voices.json", "w") as f:
        json.dump(voices, f)
    return voices