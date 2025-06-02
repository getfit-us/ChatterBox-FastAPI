from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import sys
import uuid
import re

import torchaudio as ta
from dotenv import load_dotenv
from audio.convert_audio import join_audio_files
from tts.model import get_model
from config.constants import AUDIO_TEMP_DIRECTORY_SIZE_LIMIT


# Helper to determine if the process is managed by Uvicorn's reloader
def is_reloader_process():
    """Check if the current process is a uvicorn reloader"""
    return (
        sys.argv[0].endswith("_continuation.py")
        or os.environ.get("UVICORN_STARTED") == "true"
    )


# Flag to prevent duplicate notifications
IS_RELOADER = is_reloader_process()
if not IS_RELOADER:
    os.environ["UVICORN_STARTED"] = "true"


load_dotenv()


def limit_audio_temp_directory_size():
    """Limit the size of the audio temp directory to the AUDIO_TEMP_DIRECTORY_SIZE_LIMIT"""
    if os.path.exists("audio_temp"):
        files = [os.path.join("audio_temp", f) for f in os.listdir("audio_temp") if os.path.isfile(os.path.join("audio_temp", f))]
        files.sort(key=lambda x: int(x.split("_")[-1]))  # sort by modification time
        total_size = sum(os.path.getsize(f) for f in files)
        while total_size > AUDIO_TEMP_DIRECTORY_SIZE_LIMIT and files:
            file_to_remove = files.pop(0)
            total_size -= os.path.getsize(file_to_remove)
            os.remove(file_to_remove)


def split_text_into_chunks(text: str, chunk_size: int = 1000):
    """Split text into chunks of around chunk_size, respecting sentence boundaries."""
    # Split text into sentences using regex
    sentence_endings = re.compile(r'(?<=[.!?]) +')
    sentences = sentence_endings.split(text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        # If adding this sentence would exceed the chunk size, start a new chunk
        if current_chunk and len(current_chunk) + len(sentence) + 1 > chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def generate_audio(text: str,  exaggeration: float = 0.5, cfg_weight: float = 0.5, output_path: str = None, voice_path: str = None, batching: bool = False):
    """Generate audio from text using ChatterboxTTS"""
    limit_audio_temp_directory_size()
    model = get_model()

    if batching:
        # Split text into chunks of 1000 characters, we need to make sure we don't split in the middle of a word or sentence
        chunks = split_text_into_chunks(text, 1000)
        chunk_files = []
        if not chunks:
            raise ValueError("No chunks generated")
        for idx, chunk in enumerate(chunks):
          
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())
            chunk_output_path = f"outputs/chunk_{idx}_{timestamp}_{unique_id}.wav"
            generate_audio(
                text=chunk,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                output_path=chunk_output_path,
                voice_path=voice_path,
            )
            chunk_files.append(chunk_output_path)
        join_audio_files(chunk_files, output_path)
        # clean up chunk files
        for f in chunk_files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"Error removing chunk file {f}: {e}")
        return  output_path

    # Generate the audio
    audio = model.generate(text,  exaggeration=exaggeration, cfg_weight=cfg_weight, audio_prompt_path=voice_path)

    if output_path:
        ta.save(output_path, audio, model.sr)

    return (model.sr, audio.squeeze(0).numpy())


if __name__ == "__main__":
    audio = generate_audio("What does your default voice sound like?")
