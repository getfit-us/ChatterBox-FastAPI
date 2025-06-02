import torch
from chatterbox.tts import ChatterboxTTS

model = None


def get_model():
    global model
    if model is None:
        model = load_tts_model()
    return model


def load_tts_model():

    if torch.cuda.is_available():
        print("Using CUDA")
        device = "cuda"
    elif torch.backends.mps.is_available():
        print("Using MPS")
        device = "mps"
    else:
        print("Using CPU")
        device = "cpu"

    map_location = torch.device(device)
    torch_load_original = torch.load

    def patched_torch_load(*args, **kwargs):
        if "map_location" not in kwargs:
            kwargs["map_location"] = map_location
        return torch_load_original(*args, **kwargs)

    torch.load = patched_torch_load
    global model
    model = ChatterboxTTS.from_pretrained(device=device)

    return model


def unload_tts_model():
    """Unload the TTS model"""
    global model
    model = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
