import os
import uuid
import datetime
from google import genai
from dotenv import load_dotenv
from google.cloud import aiplatform

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = "us-central1"
PROMPT_FILE = "prompt.txt"
VIDEO_FOLDER = "videos"
MODEL=os.getenv("MODEL")
MODEL_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL}"
VIDEO_LENGTH = "8s"
ASPECT_RATIO = "9:16"

# Initialize the Vertex AI client
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION
)

def load_prompt_from_file(file_path):
    """Reads and returns the content of a text file."""
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Prompt file not found at '{file_path}'")
        return None

def generate_video(prompt):
    """Generates a video using Vertex AI with a given prompt."""
    print("Generating video...")
    if not prompt:
        return None

    generation_config = {
        "prompt": prompt,
        "aspectRatio": ASPECT_RATIO,
        "videoLength": VIDEO_LENGTH,
    }

    try:
        client = aiplatform.gapic.PredictionServiceClient(
            client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
        )

        instances = [generation_config]

        response = client.predict(
            endpoint=MODEL_NAME,
            instances=instances
        )
        
        if response.predictions:
            print("Video generation started. Waiting for operation to complete...")
            # The response contains a unique operation ID to track the job.
            return response.predictions[0]["operation"]
        else:
            print("No video generation predictions were returned.")
            return None

    except Exception as e:
        print(f"An error occurred during video generation: {e}")
        return None


def get_video_from_operation(operation_name):
    """Fetches the generated video from the completed operation."""
    try:
        operation = aiplatform.gapic.Operation(name=operation_name)
        # This polls the operation until it's done.
        video_response = operation.wait(timeout=600)
        return video_response
    except Exception as e:
        print(f"An error occurred while waiting for the video operation: {e}")
        return None


def save_video(response, folder_path):
    """Saves the generated video to a file with a unique name."""
    if not response or not response.generated_videos:
        print("Video generation failed. No videos were returned.")
        return

    # Ensure the target folder exists
    os.makedirs(folder_path, exist_ok=True)
    
    generated_video_bytes = response.generated_videos[0].video.bytes
    
    # Generate a unique filename using a timestamp and UUID
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    video_file_name = f"portrait_video_{timestamp}_{unique_id}.mp4"
    file_path = os.path.join(folder_path, video_file_name)

    with open(file_path, "wb") as f:
        f.write(generated_video_bytes)
    print(f"Video successfully generated and saved as {file_path}")

def main():
    """Main function to orchestrate the video generation process."""
    prompt = load_prompt_from_file(PROMPT_FILE)
    if not prompt:
        return

    # First, start the video generation job
    operation_name = generate_video(prompt)
    if not operation_name:
        return

    # Then, wait for the job to complete and get the video
    video_response = get_video_from_operation(operation_name)
    if not video_response:
        return

    # Finally, save the video
    save_video(video_response, VIDEO_FOLDER)

if __name__ == "__main__":
    main()