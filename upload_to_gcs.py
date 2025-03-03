from google.cloud import storage


def upload_to_gcs(bucket_name, local_file_path, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""

    # Initialize a client
    client = storage.Client()

    # Get the bucket
    bucket = client.bucket(bucket_name)

    # Create a new blob (object) in the bucket
    blob = bucket.blob(destination_blob_name)

    # Upload the file
    blob.upload_from_filename(local_file_path)

    print(
        f"File {local_file_path} uploaded to gs://{bucket_name}/{destination_blob_name}"
    )


# Replace with your details
bucket_name = "xaimail"  # Change this
local_file_path = "A:/xai.xai"  # Change this
destination_blob_name = "xai.txt"  # Name of file in GCS

upload_to_gcs(bucket_name, local_file_path, destination_blob_name)
