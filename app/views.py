from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, UnidentifiedImageError
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
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return HttpResponse("No file uploaded. Please try again.", status=400)

        language = request.POST.get('language', 'en')
        file_name = uploaded_file.name
        uploaded_path = os.path.join(UPLOADED_IMAGES_DIR, file_name)

        # Save the uploaded file to the server
        try:
            with open(uploaded_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
        except Exception as e:
            return HttpResponse(f"Error saving file: {str(e)}", status=500)

        # Validate and open the image
        try:
            image = Image.open(uploaded_path)
            image.verify()  # Verify the file integrity
            image = Image.open(uploaded_path)  # Reopen for processing
        except UnidentifiedImageError:
            os.remove(uploaded_path)  # Remove invalid file
            return HttpResponse('The uploaded file is not a valid image. Please try again.', status=400)

        # Perform OCR and process the image
        try:
            ocr_text = pytesseract.image_to_string(image)
            result = parse_ocr_text(ocr_text)
            result['full_text'] = translate_text(ocr_text, language)

            # Store results and image path in the session
            request.session['result'] = result
            request.session['uploaded_image'] = file_name

            return redirect('result')
        except Exception as e:
            return HttpResponse(f"Error processing image: {str(e)}", status=500)

    return HttpResponse('Invalid request method.', status=405)


def result_page(request):
    """Render the result page with OCR data and uploaded image."""
    result = request.session.get('result', {})
    uploaded_image = request.session.get('uploaded_image', None)

    # Construct the full image path to serve it correctly in the template
    uploaded_image_url = f'/media/uploaded_images/{uploaded_image}' if uploaded_image else None

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
