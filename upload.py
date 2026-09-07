import boto3
from botocore.client import Config

# Connect to MinIO
s3 = boto3.client('s3',
    endpoint_url='http://localhost:9001',
    aws_access_key_id='admin',       # Replace with your MINIO_ROOT_USER if different
    aws_secret_access_key='password', # Replace with your MINIO_ROOT_PASSWORD if different
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

bucket_name = 'conversation-intelligence'

# Create the bucket if it doesn't exist
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' already exists.")
except Exception:
    print(f"Creating bucket '{bucket_name}'...")
    s3.create_bucket(Bucket=bucket_name)

# Upload the files
print("Uploading audio.wav...")
s3.upload_file(
    'audio3.wav', # Your local path
    bucket_name, 
    'raw/audio3.wav' # The path in MinIO
)

print("Uploading sample_prompts.csv...")
s3.upload_file(
    'sample_prompts.csv', # Your local path
    bucket_name, 
    'prompts/sample_prompts.csv' # The path in MinIO
)

print("✅ Upload complete!")
