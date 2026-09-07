import os
import shutil

import kagglehub


def main():
    print("Downloading dataset via kagglehub...")
    # Download latest version
    path = kagglehub.dataset_download("axondata/call-center-speech-dataset")
    print(f"Dataset downloaded to cache at: {path}")

    # Create the local dataset directory
    local_dataset_dir = os.path.join(os.getcwd(), "dataset")
    os.makedirs(local_dataset_dir, exist_ok=True)

    print(f"Copying files to {local_dataset_dir} ...")
    
    # Copy files from the cache path to the local dataset directory
    for item in os.listdir(path):
        s = os.path.join(path, item)
        d = os.path.join(local_dataset_dir, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
            
    print("Dataset successfully copied to the 'dataset' folder!")

if __name__ == "__main__":
    main()
