# ChatterBox-FASTAPI by Chris Scott
# https://github.com/getfit-us/ChatterBox-FastAPI
# Description: Main FastAPI server for ChatterBox Text-to-Speech

from contextlib import asynccontextmanager
import os
import time
from datetime import datetime
import uuid
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import markdown2
from audio.audio_utils import convert_to_wav
from audio.convert_audio import join_audio_files
from tts.inference import generate_audio
from tts.model import load_tts_model, unload_tts_model
from tts.voices import add_voice, get_voice_by_name, get_voices

# Delete restart.flag if it exists (to ensure clean restart)
if os.path.exists("restart.flag"):
    try:
        os.remove("restart.flag")
        print("🗑️ restart.flag deleted on startup.")
    except Exception as e:
        print(f"⚠️ Could not delete restart.flag: {e}")

# Function to ensure .env file exists
def ensure_env_file_exists():
    """Create a .env file from defaults and OS environment variables"""
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        try:
            # 1. Create default env dictionary from .env.example
            default_env = {}
            with open(".env.example", "r") as example_file:
                for line in example_file:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key = line.split("=")[0].strip()
                        default_env[key] = line.split("=", 1)[1].strip()

            # 2. Override defaults with Docker environment variables if they exist
            final_env = default_env.copy()
            for key in default_env:
                if key in os.environ:
                    final_env[key] = os.environ[key]

            # 3. Write dictionary to .env file in env format
            with open(".env", "w") as env_file:
                for key, value in final_env.items():
                    env_file.write(f"{key}={value}\n")

            print(
                "✅ Created default .env file from .env.example and environment variables."
            )
        except Exception as e:
            print(f"⚠️ Error creating default .env file: {e}")


# Ensure .env file exists before loading environment variables
ensure_env_file_exists()

# Load environment variables from .env file
load_dotenv(override=True)

from fastapi import FastAPI, Request, Form, HTTPException, Depends, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

model = None


@asynccontextmanager
async def startup_event(app: FastAPI):
    # Startup logic
    global model
    if model is None:
        print("Loading Chatterbox TTS model")
        model = load_tts_model()

    print("Model loaded")
  
    yield
    # Shutdown logic (optional)
    print("Model unloaded")
    unload_tts_model()


# Create FastAPI app
app = FastAPI(
    title="Chatterbox-FASTAPI",
    description="High-performance Text-to-Speech server using Chatterbox-FASTAPI",
    version="1.0.0",
    lifespan=startup_event,
)


# after the model is loaded, load the custom voice interface
from ui.custom_voice import voice_interface
import gradio as gr




# Ensure directories exist
os.makedirs("outputs", exist_ok=True)
os.makedirs("voices", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Mount directories for serving files
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/voices", StaticFiles(directory="voices"), name="voices")



print("Mounting custom voice interface")
app = gr.mount_gradio_app(app, voice_interface, path="/custom_voice")

# API models
class SpeechRequest(BaseModel):
    input: str
    model: str = "orpheus"
    voice: str = "default"
    response_format: str = "wav" 
    speed: float = 1.0


class APIResponse(BaseModel):
    status: str
    voice: str
    output_file: str
    generation_time: float


class CustomVoiceRequest(BaseModel):
    audio_file: str
    voice_name: str
    exaggeration: float
    cfg_weight: float


# OpenAI-compatible API endpoint
@app.post("/v1/audio/speech")
async def create_speech_api(request: SpeechRequest):
    """
    Generate speech from text using the Orpheus TTS model.
    Compatible with OpenAI's /v1/audio/speech endpoint.
    """
    if not request.input:
        raise HTTPException(status_code=400, detail="Missing input text")

    voice_obj = get_voice_by_name(request.voice)
    if not voice_obj and request.voice is not None and request.voice != "default":
        raise HTTPException(status_code=400, detail=f"Voice '{request.voice}' not found")
    voice_path = voice_obj["path"] if voice_obj else None
    exaggeration = voice_obj["exaggeration"] if voice_obj else 0.5
    cfg_weight = voice_obj["cfg_weight"] if voice_obj else 0.4

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())
    output_path = f"outputs/{timestamp}_{unique_id}.wav"

    # handle batching (1000 characters per chunk) 
    if len(request.input) > 1000:
        print(f"Using batching for long text from web form ({len(request.input)} characters)")

        generate_audio(
            voice_path=voice_path,
            text=request.input,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            output_path=output_path,
            batching=True,
        )
        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=os.path.basename(output_path),
        )

    if voice_path:
        generate_audio(
            voice_path=voice_path,
            text=request.input,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            output_path=output_path,
        )
    else:
        generate_audio(
            text=request.input,
            output_path=output_path,
        )

    # Return audio file
    return FileResponse(
        path=output_path,
        media_type="audio/wav",
        filename=f"{timestamp}_{unique_id}.wav",
    )


@app.get("/v1/audio/voices")
async def list_voices():
    """Return list of available voices"""
    voices = get_voices()
    voice_list = [{"name": voice["name"], "path": voice["path"]} for voice in voices]
    return JSONResponse(content={"status": "ok", "voices": voice_list})


@app.get("/v1/audio/models")
async def list_models():
    """Return list of available models"""
    return JSONResponse(content={"status": "ok", "models": ["chatterbox"]})


# Legacy API endpoint for compatibility
@app.post("/speak")
async def speak(request: Request):
    """Legacy endpoint for compatibility with existing clients"""
    data = await request.json()
    text = data.get("text", "")
    voice = data.get("voice", "Default")

    if not text:
        return JSONResponse(status_code=400, content={"error": "Missing 'text'"})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())
    output_path = f"outputs/{voice}_{timestamp}_{unique_id}.wav"
    voices = get_voices()
    voice_path = None
    exaggeration = 0.5
    cfg_weight = 0.4
    
    if voice in [voice["name"] for voice in voices]:
        voice_obj = next((voice for voice in voices if voice["name"] == voice), None)
        if voice_obj:
            voice_path = voice_obj["path"]
            exaggeration = voice_obj["exaggeration"]
            cfg_weight = voice_obj["cfg_weight"]
    
    if len(text) > 1000:
        print(f"Using batching for long text from web form ({len(text)} characters)")
    
     
        
        # Split text into chunks
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        chunk_files = []
        for chunk in chunks:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())
            chunk_output_path = f"outputs/{timestamp}_{unique_id}.wav"
            generate_audio(
                text=chunk,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                output_path=chunk_output_path,
                voice_path=voice_path,
            )
            chunk_files.append(chunk_output_path)
        # Join all chunk files into one
        final_output_path = f"outputs/{timestamp}_{unique_id}_joined.wav"
        join_audio_files(chunk_files, final_output_path)
        # Optionally, clean up chunk files
        for f in chunk_files:
            try:
                os.remove(f)
            except Exception:
                pass
        return FileResponse(
            path=final_output_path,
            media_type="audio/wav",
            filename=os.path.basename(final_output_path),
        )
    
   

    start = time.time()
    if voice_path:
        generate_audio(
            voice_path=voice_path,
            text=text,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            output_path=output_path,
        )
    else:
        generate_audio(text=text, output_path=output_path)
    end = time.time()
    generation_time = round(end - start, 2)

    return JSONResponse(
        content={
            "status": "ok",
            "voice": voice,
            "output_file": output_path,
            "generation_time": generation_time,
        }
    )


@app.post("/v1/audio/custom_voice")
async def custom_voice(
    audio_file: UploadFile = File(...),
    voice_name: str = Form(...),
    exaggeration: float = Form(...),
    cfg_weight: float = Form(...)
):
    # Save the uploaded file
    file_location = f"voices/{voice_name}.{audio_file.filename.split('.')[-1]}"
    with open(file_location, "wb") as f:
        f.write(await audio_file.read())

    # Now use file_location as the path to the audio file
    audio_type = audio_file.filename.split(".")[-1]
    if audio_type not in ["wav", "mp3", "m4a", "ogg", "flac"]:
        return JSONResponse(
            content={"status": "error", "message": "Invalid audio file type."}
        )

    if audio_type != "wav":
        # convert audio file to wav
        wav_path = f"voices/{voice_name}.wav"
        convert_to_wav(file_location, wav_path)
        file_location = wav_path

    voice = {
        "name": voice_name,
        "path": file_location,
        "exaggeration": exaggeration,
        "cfg_weight": cfg_weight
    }
    add_voice(voice)

    return JSONResponse(
        content={"status": "ok", "message": "Custom voice generated successfully."}
    )





@app.get("/get_config")
async def get_config():
    """Get current configuration from .env file or defaults"""
    config = get_current_config()
    return JSONResponse(content=config)


@app.post("/save_config")
async def save_config(request: Request):
    """Save configuration to .env file"""
    data = await request.json()

    # Convert values to proper types
    for key, value in data.items():
        if key in [
            "CHATTERBOX_PORT",
            "AUDIO_TEMP_DIRECTORY_SIZE_LIMIT",
            "CHATTERBOX_HOST"
        ]:
            try:
                data[key] = str(int(value))
            except (ValueError, TypeError):
                pass
        

    # Write configuration to .env file
    with open(".env", "w") as f:
        for key, value in data.items():
            f.write(f"{key}={value}\n")

    return JSONResponse(
        content={
            "status": "ok",
            "message": "Configuration saved successfully. Restart server to apply changes.",
        }
    )


@app.post("/restart_server")
async def restart_server():
    """Restart the server by touching a file that triggers Uvicorn's reload"""
    import threading

    def touch_restart_file():
        # Wait a moment to let the response get back to the client
        time.sleep(0.5)

        # Create or update restart.flag file to trigger reload
        restart_file = "restart.flag"
        with open(restart_file, "w") as f:
            f.write(str(time.time()))

        print("🔄 Restart flag created, server will reload momentarily...")

    # Start the touch operation in a separate thread
    threading.Thread(target=touch_restart_file, daemon=True).start()

    # Return success response
    return JSONResponse(
        content={
            "status": "ok",
            "message": "Server is restarting",
        }
    )


def get_current_config():
    """Read current configuration from .env.example and .env files"""
    # Default config from .env.example
    default_config = {}
    if os.path.exists(".env.example"):
        with open(".env.example", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    default_config[key] = value

    # Current config from .env
    current_config = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    current_config[key] = value

    # Merge configs, with current taking precedence
    config = {**default_config, **current_config}

    # Add current environment variables
    for key in config:
        env_value = os.environ.get(key)
        if env_value is not None:
            config[key] = env_value

    return config


@app.get("/api-docs", response_class=HTMLResponse)
async def api_docs():
    with open("API_REFERENCE.md", "r") as f:
        content = f.read()
    
    css = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1, h2, h3, h4 {
            color: #2c3e50;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        code {
            background-color: #f6f8fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
        }
        pre {
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }
        th, td {
            border: 1px solid #dfe2e5;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background-color: #f6f8fa;
        }
        blockquote {
            border-left: 4px solid #dfe2e5;
            margin: 0;
            padding-left: 16px;
            color: #6a737d;
            border-radius: 4px;
            box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
            
        }
    </style>
    """
    
    html = markdown2.markdown(content, extras=['tables', 'fenced-code-blocks'])
    return HTMLResponse(content=css + html)


if __name__ == "__main__":
    import uvicorn

    # Check for required settings
    required_settings = ["CHATTERBOX_PORT", "CHATTERBOX_HOST"]
    missing_settings = [s for s in required_settings if s not in os.environ]
    if missing_settings:
        print(f"⚠️ Missing environment variable(s): {', '.join(missing_settings)}")
        print("   Using fallback values for server startup.")

    # Get host and port from environment variables with better error handling
    try:
        host = os.environ.get("CHATTERBOX_HOST")
        if not host:
            print("⚠️ CHATTERBOX_HOST not set, using 0.0.0.0 as fallback")
            host = "0.0.0.0"
    except Exception:
        print("⚠️ Error reading CHATTERBOX_HOST, using 0.0.0.0 as fallback")
        host = "0.0.0.0"

    try:
        port = int(os.environ.get("CHATTERBOX_PORT", "8880"))
    except (ValueError, TypeError):
        print("⚠️ Invalid CHATTERBOX_PORT value, using 8880 as fallback")
        port = 5005

    print(f"🔥 Starting Chatterbox-FASTAPI Server on {host}:{port}")
    print(
        f"💬 Web UI available at http://{host if host != '0.0.0.0' else 'localhost'}:{port}"
    )
    print(
        f"📖 API docs available at http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs"
    )

    # Include restart.flag in the reload_dirs to monitor it for changes
    extra_files = ["restart.flag"] if os.path.exists("restart.flag") else []

    # Start with reload enabled to allow automatic restart when restart.flag changes
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["."],
        reload_includes=["*.py", "*.html", "restart.flag"],
    )
