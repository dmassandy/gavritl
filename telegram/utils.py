import os
import requests
import logging

def validate_fields(data, required_fields):
    for field in required_fields:
        if field not in data:
            return False
    return True

def phone_norm(phone) :
    if phone.startswith('+'):
        return phone
    return '+' + phone

def phone_number_only(phone) :
    return phone.replace('+','')

def download_file(url, download_directory):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    file_path = os.path.join(download_directory, local_filename)
    logging.info('Downloading file %s', local_filename)
    with open(file_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return (local_filename, file_path)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

def get_filename(file_path):
    local_filename = file_path.split('/')[-1]
    return local_filename