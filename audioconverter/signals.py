import threading
from django.core.signals import request_finished
from django.dispatch import receiver
import os
from django.conf import settings

@receiver(request_finished)
def trigger(sender, **kwargs):
    threading.Timer(300, cleanup_folders).start()

def cleanup_folders(**kwargs):
    input_folder = os.path.join(settings.MEDIA_ROOT, 'input')
    output_folder = os.path.join(settings.MEDIA_ROOT)

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
