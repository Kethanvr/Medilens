from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
from PIL import Image
import pytesseract
import re
import io
import base64
from gtts import gTTS
from deep_translator import GoogleTranslator
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

# Helper function to parse OCR text
def parse_ocr_text(ocr_text):
    """
    Parses the OCR text to extract relevant fields.
    """
    data = {
        "name": re.search(r"(Name|Product Name):\s*(.+)", ocr_text, re.IGNORECASE),
        "manufacturer": re.search(r"(Manufacturer|Mfg. by):\s*(.+)", ocr_text, re.IGNORECASE),
        "composition": re.search(r"(Composition|Ingredients):\s*(.+)", ocr_text, re.IGNORECASE),
        "expiry_date": re.search(r"(Expiry Date|Exp. Date):\s*(.+)", ocr_text, re.IGNORECASE),
        "batch_number": re.search(r"(Batch Number|Batch No):\s*(.+)", ocr_text, re.IGNORECASE),
        "price": re.search(r"(Price|MRP):\s*(.+)", ocr_text, re.IGNORECASE),
        "warnings": re.search(r"(Warning|Precautions):\s*(.+)", ocr_text, re.IGNORECASE),
        "storage_instructions": re.search(r"(Storage|Keep in):\s*(.+)", ocr_text, re.IGNORECASE),
    }

    formatted_data = {}
    for key, match in data.items():
        formatted_data[key] = match.group(2).strip() if match else "No Information"

    return formatted_data


# Helper function to translate text
def translate_text(text, target_language):
    """
    Translates the given text into the target language.
    """
    try:
        return GoogleTranslator(source='auto', target=target_language).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails


@app.route('/')
def home():
    """
    Route for the home page.
    """
    return render_template('home.html')


@app.route('/product')
def product_page():
    """
    Route for the product upload page.
    """
    return render_template('product.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Route to handle image upload and OCR processing.
    """
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded.'})

    # Get the selected language from the request
    language = request.form.get('language', 'en')  # Default to English

    # Handle file upload
    file = request.files['file']
    image = Image.open(file.stream)

    # Extract OCR text
    ocr_text = pytesseract.image_to_string(image)

    # Parse structured data
    structured_data = parse_ocr_text(ocr_text)

    # Translate fields based on the selected language
    translated_data = {key: translate_text(value, language) for key, value in structured_data.items()}
    translated_data['full_text'] = translate_text(ocr_text, language)

    # Store the translated data in session
    session['result'] = translated_data

    # Redirect to the result page
    return redirect(url_for('result_page'))


@app.route('/result')
def result_page():
    """
    Route for the result page.
    """
    result = session.get('result', {})
    if not result:
        return "No data found. Please upload an image first.", 400

    return render_template('result.html', result=result)


@app.route('/generate-audio/<field>', methods=['GET'])
def generate_audio(field):
    """
    Route to generate audio for a specific field.
    """
    result = session.get('result', {})
    text = result.get(field, "No information available.")

    # Generate audio using gTTS
    tts = gTTS(text, lang='en')  # Note: gTTS supports limited languages like 'kn' and 'te'
    audio_path = f"static/audio/{field}.mp3"
    tts.save(audio_path)

    return send_file(audio_path, mimetype='audio/mpeg')


if __name__ == '__main__':
    # Ensure Tesseract OCR is properly configured
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path if needed
    app.run(debug=True, port=3000)