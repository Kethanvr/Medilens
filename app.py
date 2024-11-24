from flask import Flask, request, jsonify, render_template
from PIL import Image
import pytesseract
import re
import base64
import io
import os

app = Flask(__name__)

# Helper function to parse OCR text and extract structured data
def parse_ocr_text(ocr_text):
    """
    Parses the OCR text to extract relevant information.
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

    # Format the data and handle missing information
    formatted_data = {}
    for key, match in data.items():
        formatted_data[key] = match.group(2).strip() if match else "No Information"
    
    return formatted_data

@app.route('/')
def home():
    """
    Route for the home page.
    """
    return render_template('home.html')

@app.route('/product')
def product_page():
    """
    Route for the product page.
    """
    return render_template('product.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Route to handle image upload and OCR processing.
    """
    if 'file' not in request.files and 'file' not in request.form:
        return jsonify({'status': 'error', 'message': 'No file uploaded.'})

    # Handle file upload from form-data
    if 'file' in request.files:
        file = request.files['file']
        if not file:
            return jsonify({'status': 'error', 'message': 'No file uploaded.'})

        # Open the image and extract text
        image = Image.open(file.stream)
        ocr_text = pytesseract.image_to_string(image)

    # Handle base64-encoded image (from the camera)
    elif 'file' in request.form:
        image_data = request.form['file']
        try:
            # Decode the base64 image
            image_data = image_data.split(",")[1]  # Remove the "data:image/png;base64," prefix
            image = Image.open(io.BytesIO(base64.b64decode(image_data)))
            ocr_text = pytesseract.image_to_string(image)
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Invalid image data.'})

    # Debugging: print the OCR text
    print("OCR Text:", ocr_text)

    # Parse structured data
    structured_data = parse_ocr_text(ocr_text)

    # Return the extracted data as JSON
    return jsonify({
        'status': 'success',
        'name': structured_data.get('name', 'No Information'),
        'manufacturer': structured_data.get('manufacturer', 'No Information'),
        'composition': structured_data.get('composition', 'No Information'),
        'expiry_date': structured_data.get('expiry_date', 'No Information'),
        'batch_number': structured_data.get('batch_number', 'No Information'),
        'price': structured_data.get('price', 'No Information'),
        'warnings': structured_data.get('warnings', 'No Information'),
        'storage_instructions': structured_data.get('storage_instructions', 'No Information'),
        'full_text': ocr_text  # Include the full extracted text
    })

if __name__ == '__main__':
    # Ensure Tesseract OCR is installed and available in PATH
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path if needed
    app.run(debug=True, port=3000)
