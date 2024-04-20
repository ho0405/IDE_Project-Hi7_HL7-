from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
import cv2
import numpy as np
import re
import os
import tempfile
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
import shutil
import platform  # Import the platform module

app = Flask(__name__)
CORS(app, resources={
    r"/upload": {"origins": "*"},
    r"/login-history": {"origins": "*"},
    r"/activity-history": {"origins": "*"},
})

# OS-specific configurations for Tesseract and Poppler
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    POPPLER_PATH = r'C:\Program Files\poppler-24.02.0\Library\bin'  # Adjust your Poppler bin path as needed
else:
    pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'  # Default path for Unix
    POPPLER_PATH = None  # On Unix-like systems, Poppler is usually in the PATH by default

def is_checkbox_checked(cnt, thresh):
    x, y, w, h = cv2.boundingRect(cnt)
    aspect_ratio = w / float(h)
    if 0.8 < aspect_ratio < 1.2 and 20.5 < w < 26 and 20.5 < h < 26:
        roi = thresh[y:y+h, x:x+w]
        non_zero_pixels = cv2.countNonZero(roi)
        total_pixels = w * h
        fill_ratio = non_zero_pixels / total_pixels
        return fill_ratio > 0.573
    return False

def extract_text_near_checkbox(checked_checkboxes, data, margin=50):
    text_near_checkboxes = []
    for (x, y, w, h) in checked_checkboxes:
        x_start = x + w
        y_start = y - margin
        x_end = x_start + 200
        y_end = y + h + margin

        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 60:
                x_text = int(data['left'][i])
                y_text = int(data['top'][i])
                w_text = int(data['width'][i])
                h_text = int(data['height'][i])

                if (x_start < x_text < x_end) and (y_start < y_text < y_end or y_start < y_text + h_text < y_end):
                    text_near_checkboxes.append(data['text'][i])
    return text_near_checkboxes

def extract_info_from_text(text):
    patterns = {
        'Name': r"Name:\s*(.*)",
        'AHC/WCB#': r"AHC/WCB\s*#:\s*(.*)",
        'Address': r"Address:\s*(.*)",
        'Date of Birth': r"Date of Birth:\s*(.*)",
        'Phone Number': r"Phone:\s*(.*)",
        'Referring Physician': r"Referring Physician:\s*(.*)"
    }
    info = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            info[key] = match.group(1).strip()
        else:
            info[key] = 'Not found'
    return info

def create_hl7_message(info):
    hl7_message = "MSH|^~\\&|EXA|PUREFORM|MIKATA|PUREFORM|{timestamp}||ORM^O01^ORM_O01|{control_id}||2.3|||AL||||\n".format(
        timestamp=info.get('Date of Birth', '20240311090037'),
        control_id=info.get('AHC/WCB#', '12586231')
    )
    hl7_message += "PID|1|^^^AB|{patient_id}^^^PDI|^^^AB|{name}^^^^||{dob}|{gender}|||{address}^^{city}^AB^T2H 0L8^CANADA||{phone}|||\n".format(
        patient_id=info.get('AHC/WCB#', ''),
        name=info.get('Name', ''),
        dob=info.get('Date of Birth', ''),
        gender='F',
        address=info.get('Address', ''),
        city=info.get('City', ''), 
        phone=info.get('Phone Number', '')
    )
    hl7_message += f"PV1||O|^^^{info.get('Referring Physician', '')}\n"
    return hl7_message

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf']

@app.route('/upload', methods=['POST'])
def upload_and_convert():
    if 'file' not in request.files:
        raise BadRequest('No file part')
    file = request.files['file']
    if file.filename == '':
        raise BadRequest('No selected file')
    
    if not allowed_file(file.filename):
        raise BadRequest('Unsupported file type')
    
    filename = secure_filename(file.filename)
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, filename)
        file.save(pdf_path)
        
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        combined_text = ''
        for image in images:
            text = pytesseract.image_to_string(image)
            combined_text += text + "\n"
            
        info = extract_info_from_text(combined_text)
        hl7_message = create_hl7_message(info)
        
        response = Response(hl7_message, mimetype='text/plain')
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.hl7"
        return response

if __name__ == '__main__':
    app.run(debug=True)