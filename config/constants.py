import os
from dotenv import load_dotenv

load_dotenv()

# Audio temp directory size limit in megabytes
AUDIO_TEMP_DIRECTORY_SIZE_LIMIT = int(os.getenv("AUDIO_TEMP_DIRECTORY_SIZE_LIMIT", "2000").split()[0])  



# Chatterbox port
CHATTERBOX_PORT = os.getenv("CHATTERBOX_PORT")

# Chatterbox host
CHATTERBOX_HOST = os.getenv("CHATTERBOX_HOST")
