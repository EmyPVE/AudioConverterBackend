# audioconverter/views.py
import os
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from audioconverter.forms import AudioUploadForm
from .utils import convert_audio

@csrf_exempt
def convert_upload(request):
    if request.method == 'POST':
        form = AudioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            audio_file = form.cleaned_data['audio_file']
            audio_format = request.POST.get('conversion_format', 'mp3')  # Default to 'mp3' if not provided
            print('Received file:', audio_file.name, 'Format:', audio_format)

            file_path = os.path.join(settings.MEDIA_ROOT, 'input', audio_file.name)
            with open(file_path, 'wb') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            try:
                converted_file = convert_audio(file_path, audio_format)

                return JsonResponse({'success': True, 'converted_file': converted_file})
            except ValueError as ve:
                return JsonResponse({'success': False, 'error': str(ve)})

    else:
        form = AudioUploadForm()

    return render(request, 'upload_audio.html', {'form': form})
