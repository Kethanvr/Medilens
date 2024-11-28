from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import pytesseract
from gtts import gTTS
import os
from .utils import parse_ocr_text, translate_text  # Assuming you modularized helpers

# Ensure media directories exist
MEDIA_DIR = 'media'
UPLOADED_IMAGES_DIR = os.path.join(MEDIA_DIR, 'uploaded_images')
GENERATED_AUDIO_DIR = os.path.join(MEDIA_DIR, 'generated_audio')
os.makedirs(UPLOADED_IMAGES_DIR, exist_ok=True)
os.makedirs(GENERATED_AUDIO_DIR, exist_ok=True)

def home(request):
    """Render the home page."""
    return render(request, 'home.html')

def product_page(request):
    """Render the product upload page."""
    return render(request, 'product.html')

@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        language = request.POST.get('language', 'en')

        # Ensure the uploaded_images directory exists
        uploaded_path = os.path.join('media', 'uploaded_images')
        os.makedirs(uploaded_path, exist_ok=True)
        saved_file_path = os.path.join(uploaded_path, uploaded_file.name)

        with open(saved_file_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Perform OCR and store results
        image = Image.open(saved_file_path)
        ocr_text = pytesseract.image_to_string(image)
        result = parse_ocr_text(ocr_text)
        result['full_text'] = translate_text(ocr_text, language)

        # Save result and file path in the session
        request.session['result'] = result
        request.session['uploaded_image'] = uploaded_file.name  # Store just the filename

        return redirect('result')

    return HttpResponse('Invalid method', status=405)


def result_page(request):
    result = request.session.get('result', {})
    uploaded_image = request.session.get('uploaded_image', None)

    # Construct the full image path to serve it correctly in the template
    if uploaded_image:
        uploaded_image_url = f'/media/uploaded_images/{uploaded_image}'
    else:
        uploaded_image_url = None

    return render(request, 'result.html', {
        'result': result,
        'uploaded_image': uploaded_image_url
    })


def generate_audio(request, field):
    """Generate and serve audio for a specific OCR result field."""
    result = request.session.get('result', {})
    text = result.get(field, "No information available.")
    if not text or text.strip() == "No information available.":
        return HttpResponse("No information available to generate audio.", status=400)

    try:
        # Generate audio file
        audio_path = os.path.join(GENERATED_AUDIO_DIR, f'{field}.mp3')
        tts = gTTS(text, lang='en')
        tts.save(audio_path)
        return FileResponse(open(audio_path, 'rb'), content_type='audio/mpeg')
    except Exception as e:
        return HttpResponse(f"Error generating audio: {str(e)}", status=500)
