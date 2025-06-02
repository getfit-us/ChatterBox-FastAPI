# ChatterBox-FastAPI API Reference

## Overview
ChatterBox-FastAPI is a high-performance Text-to-Speech server that provides both OpenAI-compatible and custom endpoints for speech generation.

## Base URL
```
http://localhost:8880
```

## Authentication
No authentication is required to use the API.

## Endpoints

### Text-to-Speech Generation

#### OpenAI-Compatible Endpoint
```http
POST /v1/audio/speech
```

Generate speech from text using the ChatterBox TTS model. Compatible with OpenAI's /v1/audio/speech endpoint.

**Request Body:**
```json
{
    "input": "Text to convert to speech",
    "model": "chatterbox",
    "voice": "default",
    "response_format": "wav",
    "speed": 1.0
}
```

**Parameters:**
- `input` (string, required): The text to convert to speech
- `model` (string, optional): The model to use (default: "chatterbox")
- `voice` (string, optional): The voice to use (default: "default")
- `response_format` (string, optional): The output format wav (Currently only format)
- `speed` (float, optional): Speech speed multiplier (default: 1.0)

**Response:**
Returns an audio file in WAV format.

**Notes:**
- For text longer than 1000 characters, the API automatically uses batching
- The response is a direct audio file download

#### Legacy Endpoint
```http
POST /speak
```

Legacy endpoint for compatibility with existing clients.

**Request Body:**
```json
{
    "text": "Text to convert to speech",
    "voice": "default"
}
```

**Parameters:**
- `text` (string, required): The text to convert to speech
- `voice` (string, optional): The voice to use (default: "default")

**Response:**
```json
{
    "status": "ok",
    "voice": "voice_name",
    "output_file": "path/to/output.wav",
    "generation_time": 1.23
}
```

**Notes:**
- For text longer than 1000 characters, the API automatically uses batching
- Returns a JSON response with file path and generation time

### Voice Management

#### List Available Voices
```http
GET /v1/audio/voices
```

Returns a list of available voices.

**Response:**
```json
{
    "status": "ok",
    "voices": [
        {
            "name": "voice_name",
            "exaggeration": 0.5,
            "cfg_weight": 0.4,
        }
    ]
}
```

#### List Available Models
```http
GET /v1/audio/models
```

Returns a list of available models.

**Response:**
```json
{
    "status": "ok",
    "models": ["chatterbox"]
}
```

#### Create Custom Voice API Route
```http
POST /v1/audio/custom_voice
```

Generate a custom voice from an uploaded audio file.

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `audio_file` (file, required): The audio file to use for the custom voice. Supported formats: wav, mp3, m4a, ogg, flac.
  - `voice_name` (string, required): The name to assign to the new voice.
  - `exaggeration` (float, required): Exaggeration parameter for the voice.
  - `cfg_weight` (float, required): CFG weight parameter for the voice.

**Example curl:**
```bash
curl -X POST "http://localhost:8880/v1/audio/custom_voice" \
  -F "audio_file=@/path/to/your/voice_sample.wav" \
  -F "voice_name=MyCustomVoice" \
  -F "exaggeration=0.5" \
  -F "cfg_weight=0.4"
```

**Response:**
- 200 OK
- JSON body:
  - `status`: "ok" or "error"
  - `message`: Description of the result

**Example response:**
```json
{
  "status": "ok",
  "message": "Custom voice generated successfully."
}
```

### Configuration Management

#### Get Configuration
```http
GET /get_config
```

Get current configuration from .env file or defaults.

**Response:**
Returns the current configuration as JSON.

#### Save Configuration
```http
POST /save_config
```

Save configuration to .env file.

**Request Body:**
```json
{
    "CHATTERBOX_HOST": "0.0.0.0",
    "CHATTER_BOX_PORT": "8880",
    "AUDIO_TEMP_DIRECTORY_SIZE_LIMIT": 2000
}
```

**Response:**
```json
{
    "status": "ok",
    "message": "Configuration saved successfully. Restart server to apply changes."
}
```

#### Restart Server
```http
POST /restart_server
```

Restart the server to apply configuration changes.

**Response:**
```json
{
    "status": "ok",
    "message": "Server is restarting. Please wait a moment..."
}
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request (missing or invalid parameters)
- 500: Internal Server Error

Error responses include a JSON object with an error message:
```json
{
    "detail": "Error message"
}
```

## Examples

### Generate Speech (OpenAI-Compatible)
```bash
curl -X POST http://localhost:8880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, world!", voice: "default" }'
```

### Generate Speech (Legacy)
```bash
curl -X POST http://localhost:8880/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!"}'
```

### List Available Voices
```bash
curl http://localhost:8880/v1/audio/voices
```

### Create Custom Voice
```bash
curl -X POST http://localhost:8880/v1/audio/custom_voice \
  -H "Content-Type: application/json" \
  -d '{
    "audio_file": "path/to/audio.wav",
    "voice_name": "custom_voice",
    "exaggeration": 0.5,
    "cfg_weight": 0.4
  }'
```

## Additional Resources

- Custom Voice Web UI: Available at `/custom_voice`
