import os
import time

import requests

DATASET_DIR = "/home/onedeck/Documents/Conversational_Intelligence/conversation-intelligence/dataset/Call center data samples"
API_URL = "http://127.0.0.1:8000/api/upload"

def main():
    if not os.path.exists(DATASET_DIR):
        print(f"Dataset directory not found: {DATASET_DIR}")
        return

    print("Scanning dataset directory for audio files...")
    audio_files = []
    
    for root, _dirs, files in os.walk(DATASET_DIR):
        for file in files:
            if file.endswith((".mp3", ".wav", ".flac", ".m4a")):
                audio_files.append(os.path.join(root, file))

    print(f"Found {len(audio_files)} audio files. Limiting to 1 file for testing due to API key constraints...")
    audio_files = audio_files[:1]

    for file_path in audio_files:
        print(f"\nUploading: {os.path.basename(file_path)}")
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
                response = requests.post(API_URL, files=files)
                
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully triggered workflow: {data.get('workflow_name')} (Call ID: {data.get('call_id')})")
            else:
                print(f"❌ Failed to upload. Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")

        # Sleep briefly to not overwhelm the API
        time.sleep(2)
        
    print("\nBatch upload complete! You can monitor the progress on the dashboard or via 'kubectl get workflows -n default'")

if __name__ == "__main__":
    main()
