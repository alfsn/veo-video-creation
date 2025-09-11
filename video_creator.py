import os
import time
import datetime
import uuid
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("PROJECT_ID")
if not PROJECT_ID:
    raise ValueError("PROJECT_ID environment variable not set.")
LOCATION = "us-central1"
PROMPT_FILE = "prompt.txt"
VIDEO_FOLDER = "videos"
MODEL = os.getenv("MODEL")  # e.g., "veo-3.0-generate-001"
VIDEO_LENGTH_SECONDS = 8
ASPECT_RATIO = "9:16"

# Initialize the Google Gen AI client
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def load_prompt_from_file(file_path):
    """Reads and returns the content of a text file."""
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Prompt file not found at '{file_path}'")
        return None

def generate_video(prompt):
    """Generates a video using the Google Gen AI SDK for Python."""
    print("Generating video...")
    if not prompt:
        print("Prompt is empty. Aborting video generation.")
        return None

    try:
        # Launch long-running generation job
        operation = client.models.generate_videos(
            model=MODEL,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=ASPECT_RATIO,
                duration_seconds=VIDEO_LENGTH_SECONDS,
                number_of_videos=1,
            ),
        )
        
        operation_name = operation if isinstance(operation, str) else operation.name
        print(f"Video generation operation started. Check your progress with: gcloud alpha ai operations describe {operation_name}")
        start_time = time.time()

        # Poll until completion
        while not operation.done:
            time.sleep(15)
            operation = client.operations.get(operation)
            print(operation)

        if operation.response:
                # The generated videos are in operation.result.generated_videos.
                # We are generating one video, so we get the first one.
                # We need to return the video bytes to the save_video function.
                return operation.result.generated_videos[0].video.video_bytes
        else:
            print("Video generation failed to return a response.")
            return None

    except Exception as e:
        print(f"An error occurred during video generation: {e}")
        return None


def save_video(video_bytes, folder_path):
    """Saves the generated video to a file with a unique name."""
    try:
        if not video_bytes:
            print("Video generation failed. No video bytes returned.")
            return

        # Ensure the target folder exists
        os.makedirs(folder_path, exist_ok=True)

        # Generate a unique filename using a timestamp and UUID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        video_file_name = f"portrait_video_{timestamp}_{unique_id}.mp4"
        file_path = os.path.join(folder_path, video_file_name)

        with open(file_path, "wb") as f:
            f.write(video_bytes)
        print(f"Video successfully generated and saved as {file_path}")
    except Exception as e:
        print(f"An error occurred while saving the video: {e}")

def main():
    """Main function to orchestrate the video generation process."""
    prompt = load_prompt_from_file(PROMPT_FILE)
    if not prompt:
        return

    # Start the video generation job and wait for it to complete
    video_bytes = generate_video(prompt)
    if not video_bytes:
        return

    # Save the video
    save_video(video_bytes, VIDEO_FOLDER)

if __name__ == "__main__":
    main()