from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from PIL import Image
import pytesseract
import re
import io
import base64

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for using session

# Helper function to parse OCR text
def parse_ocr_text(ocr_text):
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

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/product')
def product_page():
    return render_template('product.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files and 'file' not in request.form:
        return jsonify({'status': 'error', 'message': 'No file uploaded.'})

    # Handle file upload from form-data
    if 'file' in request.files:
        file = request.files['file']
        image = Image.open(file.stream)
    # Handle base64-encoded image (from the camera)
    elif 'file' in request.form:
        image_data = request.form['file']
        image_data = image_data.split(",")[1]  # Remove base64 prefix
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))

    # Extract OCR text
    ocr_text = pytesseract.image_to_string(image)

    # Parse structured data
    structured_data = parse_ocr_text(ocr_text)

    # Store the extracted data in session
    session['result'] = {
        'name': structured_data.get('name', 'No Information'),
        'manufacturer': structured_data.get('manufacturer', 'No Information'),
        'composition': structured_data.get('composition', 'No Information'),
        'expiry_date': structured_data.get('expiry_date', 'No Information'),
        'batch_number': structured_data.get('batch_number', 'No Information'),
        'price': structured_data.get('price', 'No Information'),
        'warnings': structured_data.get('warnings', 'No Information'),
        'storage_instructions': structured_data.get('storage_instructions', 'No Information'),
        'full_text': ocr_text  # Include the full extracted text
    }

    # Redirect to the result page
    return redirect(url_for('result_page'))

@app.route('/result')
def result_page():
    """
    Route for the result page.
    """
    # Retrieve the result data from the session
    result = session.get('result', {})
    if not result:
        return "No data found. Please upload an image first.", 400

    return render_template('result.html', result=result)

if __name__ == '__main__':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update if needed
    app.run(debug=True, port=3000)
