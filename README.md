# ChatterBox-FastAPI

High-performance Text-to-Speech server with OpenAI-compatible API



## Key ChatterBox Details

- SoTA zeroshot TTS
- 0.5B Llama backbone
- Unique exaggeration/intensity control
- Ultra-stable with alignment-informed inference
- Trained on 0.5M hours of cleaned data
- Watermarked outputs
- Easy voice conversion script
- [Outperforms ElevenLabs](https://podonos.com/resembleai/chatterbox)

## Tips

- **General Use (TTS and Voice Agents):**
  - The default settings (`exaggeration=0.5`, `cfg_weight=0.5`) work well for most prompts.
  - If the reference speaker has a fast speaking style, lowering `cfg_weight` to around `0.3` can improve pacing.

- **Expressive or Dramatic Speech:**
  - Try lower `cfg_weight` values (e.g. `~0.3`) and increase `exaggeration` to around `0.7` or higher.
  - Higher `exaggeration` tends to speed up speech; reducing `cfg_weight` helps compensate with slower, more deliberate pacing.

## Features

- **OpenAI API Compatible**: Drop-in replacement for OpenAI's `/v1/audio/speech` endpoint
- **Custom Voice Cloning**: '/custom_voice' UI Generate, Sample and save custom voice for reuse in API Calls
- **Smooth Transitions**: Crossfaded audio segments for seamless listening experience
  
  (Route implemented UI Coming Soon)
  ---
- TODO: **Web UI Configuration**: Configure all server settings directly from the interface
- TODO: **Dynamic Environment Variables**: Update API endpoint, timeouts, and model parameters without editing files
- TODO: **Server Restart**: Apply configuration changes with one-click server restart 



## Getting Started

 **Run without Docker:**
1. (Recommended) Create and activate a virtual environment:
     ```sh
     git clone https://github.com/getfit-us/ChatterBox-FastAPI.git &&
     cd ChatterBox-FastAPI 
     python3 -m venv .venv
     source .venv/bin/activate
     ```
2. Install dependencies:
    ```sh
    pip install --upgrade pip
    pip install -r requirements.txt
    cp .env.example .env
    ```
   
3. Run the FastAPI server:
    ```
    
    python app.py
    ```
4. The API will be available at [http://localhost:8880/docs](http://localhost:8880/docs)

 **Run with Docker Compose:**
1. Build and start the server:
    ```sh
    cd docker
    docker-compose up --build
    ```
2. The API will be available at [http://localhost:8880/docs](http://localhost:8880/docs)

3. To stop the server:
    ```sh
    docker-compose down
    ```

**Run with Docker only (no Compose):**

1. Build the image:
    ```sh
    docker build -t chatterbox-fastapi -f docker/Dockerfile .
    ```
2. Run the container:
    ```sh
    docker run --rm -p 8880:8880 \
      -v $(pwd)/outputs:/app/outputs \
      -v $(pwd)/voices:/app/voices \
      -v $(pwd)/static:/app/static \
      --env-file .env \
      chatterbox-fastapi
    ```


