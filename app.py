from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
from PIL import Image
import pytesseract
import re
import os
from gtts import gTTS
from deep_translator import GoogleTranslator

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Define folders for uploads and audio
UPLOAD_FOLDER = "uploads/"
AUDIO_FOLDER = "static/audio/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

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
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded.'})

    # Handle file upload
    file = request.files['file']
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Save the file
    file.save(filepath)

    # Debug: Print the saved file path
    print(f"File saved at: {filepath}")

    # Extract OCR text (this part remains the same)
    image = Image.open(filepath)
    ocr_text = pytesseract.image_to_string(image)

    # Parse and process the OCR text
    structured_data = parse_ocr_text(ocr_text)
    language = request.form.get('language', 'en')
    structured_data = {key: GoogleTranslator(source='auto', target=language).translate(value) for key, value in structured_data.items()}
    structured_data['full_text'] = GoogleTranslator(source='auto', target=language).translate(ocr_text)

    # Store result and file path in session
    session['result'] = structured_data
    session['uploaded_image'] = filepath

    return redirect(url_for('result_page'))
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))


@app.route('/result')
def result_page():
    result = session.get('result', {})
    uploaded_image = session.get('uploaded_image', None)
    if not result or not uploaded_image:
        return "No data found. Please upload an image first.", 400

    # Extract only the file name from the path
    uploaded_image_name = os.path.basename(uploaded_image)

    return render_template('result.html', result=result, uploaded_image=uploaded_image_name)

@app.route('/generate-audio/<field>', methods=['GET'])
def generate_audio(field):
    """
    Route to generate audio for a specific field.
    """
    result = session.get('result', {})
    text = result.get(field, "No information available.")
    
    if not text.strip() or text == "No Information":
        return jsonify({'status': 'error', 'message': 'No valid text to generate audio.'}), 400

    # File path for the audio
    audio_path = os.path.join(AUDIO_FOLDER, f"{field}.mp3")

    try:
        # Generate audio using gTTS
        tts = gTTS(text, lang='en')  # Modify 'lang' if needed
        tts.save(audio_path)  # Save the file
        print(f"Audio saved at: {audio_path}")  # Debugging
        return send_file(audio_path, mimetype='audio/mpeg')  # Serve the audio file
    except Exception as e:
        print(f"Error generating audio: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to generate audio.'}), 500



if __name__ == '__main__':
    # Ensure Tesseract OCR is properly configured
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    app.run(debug=True, port=3000)
