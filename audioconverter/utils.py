import os
from django.conf import settings
import subprocess

def convert_audio(input_file_path, output_format):
    valid_formats = ['mp3', 'wav', 'aiff', 'wma']
    if output_format not in valid_formats:
        raise ValueError(f'Invalid output format. Accepted formats are: {", ".join(valid_formats)}')
    output_file = f"{os.path.splitext(os.path.basename(input_file_path.replace(' ', ' ')))[0]}.{output_format}"
    output_path = os.path.join(settings.MEDIA_ROOT, output_file)

    codec = 'libmp3lame' if output_format == 'mp3' else 'pcm_s16le' 

    command = f'ffmpeg -y -i "{input_file_path}" -acodec {codec} "{output_path}"'

    subprocess.run(command, shell=True)

    return output_file