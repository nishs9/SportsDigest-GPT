import os
import zipfile
import argparse
from google.cloud import storage

# Sets up the argparse object to parse command line arguments
def setup_argparse():
    parser = argparse.ArgumentParser(description='Create a zip file.')
    parser.add_argument('filename', type=str, help='The name of the zip file to create.')
    args = parser.parse_args()
    return args

# Zips up the codebase for deployment to GCP
def zip_codebase(ziph, custom_zip_path='.'):
    for root, ___, files in os.walk(custom_zip_path):
        for file in files:
            if file.endswith('.zip'):
                continue 
            file_path = os.path.join(root, file)
            if custom_zip_path != '.':
                file_path = os.path.relpath(file_path, custom_zip_path)
            ziph.write(file_path)

# Uploads the zip file to the GCP bucket
def upload_to_bucket(blob_name, path_to_file, bucket_name):
    storage_client = storage.Client.from_service_account_json('secrets/sportsdigest-gpt-2b26ac3dcfa4.json')
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)
    return print("File {} successfully uploaded to {}.".format(path_to_file, bucket_name))

if __name__ == '__main__':
    args = setup_argparse()
    zipf = zipfile.ZipFile(args.filename, 'w', zipfile.ZIP_DEFLATED)
    zip_codebase(zipf)
    zipf.close()
    upload_to_bucket(args.filename, args.filename, 'sportsdigest-gpt-code-bucket')
