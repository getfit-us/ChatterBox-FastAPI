import json
import shutil
import sys
from pathlib import Path

from audio.audio_utils import convert_to_wav


sys.path.append(str(Path(__file__).parent.parent))  # Adds the parent directory to path
import gradio as gr
from tts.inference import generate_audio
from tts.voices import get_voices




def save_voice(audio_file, voice_name, exaggeration = 0.5, cfg_weight = 0.5):
    
    if not voice_name:
        gr.Warning("Please enter a voice name.")
        return None, None, None
    if not audio_file:
        gr.Warning("Recording or uploading an audio sample is required.")
        return None, None, None
    
    #convert the audio file to wav
    if audio_file.split(".")[-1] != "wav":
        print("Converting audio to wave format.")
        convert_to_wav(audio_file, f"voices/{voice_name}.wav")
    voice_name = voice_name.strip().lower()
    
    print(f"Saving new voice '{voice_name}' with audio file '{audio_file}'")
   
    
    if not voice_name:
        gr.Warning("Please enter a voice name.")
        return gr.update()
    if not audio_file:
        gr.Warning("Recording or uploading an audio sample is required.")
        return gr.update()

    print(f"Saving new voice '{voice_name}'")

    voices = get_voices()

    if voice_name and len(voices) > 0 and [voice for voice in voices if voice["name"] == voice_name]:
        gr.Warning(f"Voice '{voice_name}' already exists. Please enter a different name.")
        return gr.update()

    new_voice_path = f"voices/{voice_name}.wav"
    shutil.copy(audio_file, new_voice_path)
    # save the voice
    voices.append({"name": voice_name, "path": new_voice_path, "exaggeration": exaggeration, "cfg_weight": cfg_weight})
    with open("config/voices.json", "w") as f:
        json.dump(voices, f)
   

 

    gr.Info(f"Voice '{voice_name}' saved successfully.")

    # Return updated dropdown choices
    updated_voices = get_voices()
    return gr.update(choices=[voice["name"] for voice in updated_voices] if updated_voices else ["No user generated voices found"]), gr.update(value=None), gr.update(value="")


def delete_voice(voice_name):
    if not voice_name or voice_name == "No user generated voices found":
        gr.Warning("Please select a valid voice to delete.")
        return gr.update()
    
    voices = get_voices()
    # Remove the voice from the list
    voices = [voice for voice in voices if voice["name"] != voice_name]
    
    # Save updated voices list
    with open("config/voices.json", "w") as f:
        json.dump(voices, f)
    
    # Delete the voice file
    try:
        import os
        voice_file = f"voices/{voice_name}.wav"
        if os.path.exists(voice_file):
            os.remove(voice_file)
    except Exception as e:
        print(f"Error deleting voice file: {e}")
    
    gr.Info(f"Voice '{voice_name}' deleted successfully.")
    
    # Return updated dropdown choices
    updated_voices = get_voices()
    return gr.update(choices=[voice["name"] for voice in updated_voices] if updated_voices else ["No user generated voices found"])


def clear_action():
    return [None, ""]


def generate_sample(audio_input, generate_text_input, voice_name_input, exaggeration, cfg_weight):

    if not voice_name_input:
        voice_name_input = "custom_voice_temp"
    else:
        voice_name_input = voice_name_input.strip().lower()

        if not audio_input:
            gr.Warning("Please upload or record audio sample with microphone.")
            return None
        if not generate_text_input:
            gr.Warning("Please enter text to generate.")

            return None
        gr.Info(f"Generating sample for voice '{voice_name_input}'")
        print(
            f"Generating sample for voice '{voice_name_input}' with audio file path '{audio_input}'"
        )

        # convert the audio file to wav
        if audio_input.split(".")[-1] != "wav":
            print("Converting audio to wave format.")
            convert_to_wav(audio_input, f"voices/{voice_name_input}.wav")
            audio_input = f"voices/{voice_name_input}.wav"
        

        sr, audio = generate_audio(text=generate_text_input, output_path=f"voices/{voice_name_input}.wav", voice_path=audio_input, exaggeration=exaggeration, cfg_weight=cfg_weight)
        gr.Info(f"Sample generated successfully")
        return sr, audio


def download_recording(audio_file_path):
    """Return the audio file path for download"""
    if audio_file_path:
        return audio_file_path
    return None


def handle_notification(message, type="error"):
    if type == "error":
        gr.Error(message)
    elif type == "success":
        gr.Success(message)
    elif type == "info":
        gr.Info(message)


with gr.Blocks() as voice_interface:

    gr.Markdown(
        """
        # Custom Voice Creation
        Upload an audio sample or record with your microphone to create a custom voice.
       
        """
    )

    with gr.Row():
        with gr.Column():

            audio_input = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="Upload Audio Sample (WAV, MP3, M4A, OGG, or FLAC) or Record with Microphone",
                show_download_button=True,
            )

            generate_text_input = gr.Textbox(
                label="Enter input text for sample generation", lines=3
            )
            exaggeration = gr.Slider(
                0.25,
                2,
                step=0.05,
                label="Exaggeration (Neutral = 0.5, extreme values can be unstable)",
                value=0.5,
                interactive=True,
            )
            cfg_weight = gr.Slider(0.0, 1, step=0.05, label="CFG/Pace", value=0.5, interactive=True)

            generate_button = gr.Button(
                "Generate Sample",
                variant="primary",
            )

        with gr.Column():
            audio_output = gr.Audio(
                sources=None,
                label="Output Audio Generated",
                show_download_button=True,
                interactive=False,
            )

            voice_name_input = gr.Textbox(
                label="Voice Name", placeholder="Enter a name for your custom voice"
            )

            save_button = gr.Button("Save Voice")
           
            

            current_voices = get_voices()
            if current_voices:
                voice_dropdown = gr.Dropdown(choices=[voice["name"] for voice in current_voices], label="Custom Voices", inputs=[voice["name"] for voice in current_voices])
            else:
                voice_dropdown = gr.Dropdown(
                    choices=["No user generated voices found"],
                    label="Custom Voices",
                    interactive=False,
                )

            gr.Button(
                "Delete Voice",
                variant="stop",
            ).click(delete_voice, inputs=voice_dropdown, outputs=voice_dropdown)
            save_button.click(
                save_voice,
                inputs=[audio_input, voice_name_input, exaggeration, cfg_weight],
                outputs=[voice_dropdown, audio_input, voice_name_input]
            )

            generate_button.click(
                fn=generate_sample,
                inputs=[
                    audio_input,
                    generate_text_input,
                    voice_name_input,
                    exaggeration,
                    cfg_weight,
                ],
                outputs=[audio_output],
                show_progress_on=audio_output,
                trigger_mode="once",
            )

voice_interface.load()

# for testing
if __name__ == "__main__":
    voice_interface.launch(
        server_name="0.0.0.0",
        server_port=5005,
    )
