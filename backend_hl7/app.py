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
import datetime

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
        return fill_ratio > 0.573  # Adjust as necessary
    return False

def extract_text_near_checkbox(checked_checkboxes, data, margin=200):
    text_near_checkboxes = []
    allowed_texts = ["Abdomen", "Male", "Female", "Undisclosed", "AAA", "Liver", "Pelvis", "include kidneys", "Renal", "Thyroid", "Appendix", "Groin", "Inguinal Hernia", "Other Indication", "Abdominal Wall", "Scrotum/Testes", "Neck", "Lump/Soft Tissue", "Other", "Dating", "Nuchal", "Detailed", "Biophysical", "OBS", "Complete","Carotid","Venous","Renal","Temporal","ABI","Lower","Upper","Bone"]

    checkbox_regions = {text: [] for text in allowed_texts}

    for (x, y, w, h) in checked_checkboxes:
        x_start = x + w
        y_start = y - margin
        x_end = x_start + 30  # Adjust as necessary
        y_end = y + h + margin

        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 60:  # Confidence threshold
                x_text = int(data['left'][i])
                y_text = int(data['top'][i])
                w_text = int(data['width'][i])
                h_text = int(data['height'][i])

                if (x_start < x_text < x_end) and (y_start < y_text < y_end or y_start < y_text + h_text < y_end):
                    if data['text'][i] in allowed_texts:
                        if data['text'][i] == "Complete":
                            text_near_checkboxes.append("Complete Breast Evaluation")
                        elif data['text'][i] == "Knee":
                            text_near_checkboxes.append("Includes Baker's Cyst")
                        elif data['text'][i] == "Liver":
                            text_near_checkboxes.append("Elastography")
                        elif data['text'][i] == "Renal":
                            text_near_checkboxes.append("Kidneys & Bladder")
                        elif data['text'][i] == "Neck":
                            text_near_checkboxes.append("Salivary glands, lymph nodes")
                        elif data['text'][i] == "Hand":
                            text_near_checkboxes.append("Or Finger")
                        elif data['text'][i] == "Foot":
                            text_near_checkboxes.append("or Toe")
                        elif data['text'][i] == "Plantar":
                            text_near_checkboxes.append("Fascia")
                        elif data['text'][i] == "Muscle":
                            text_near_checkboxes.append("/Tendon")
                        elif data['text'][i] == "Complete":
                            text_near_checkboxes.append("Obstetrical Evaluation")
                        elif data['text'][i] == "Dating":
                            text_near_checkboxes.append("Viability")
                        elif data['text'][i] == "Nuchal":
                            text_near_checkboxes.append("Translucency (11w 6d - 13w 6d)")
                        elif data['text'][i] == "Detailed":
                            text_near_checkboxes.append("Exam > 18 weeks")
                        elif data['text'][i] == "Biophysical":
                            text_near_checkboxes.append("Profile")
                        elif data['text'][i] == "OBS":
                            text_near_checkboxes.append(" -Limited (Biometry, Placenta, Position, Heart-rate)")    
                        elif data['text'][i] == "Breast":
                            text_near_checkboxes.append("Biopsy")
                        elif data['text'][i] == "Thyroid":
                            text_near_checkboxes.append("Biopsy")
                        elif data['text'][i] == "Temporal":
                            text_near_checkboxes.append("Artery Doppler")
                        elif data['text'][i] == "ABI":
                            text_near_checkboxes.append("Ankle Brachial index only")
                        elif data['text'][i] == "Lower":
                            text_near_checkboxes.append("Extremity Duplex with ABI")
                        elif data['text'][i] == "Upper":
                            text_near_checkboxes.append("Extremity Duplex")
                        elif data['text'][i] == "Bone":
                            text_near_checkboxes.append("Mineral Densitometry")
                        elif data['text'][i] == "Dating":
                            text_near_checkboxes.append("Viability")
                        elif data['text'][i] == "Nuchal":
                            text_near_checkboxes.append("Translucency (11w 6d - 13w 6d)")
                        elif data['text'][i] == "Detailed":
                            text_near_checkboxes.append("Exam > 18 weeks")
                        elif data['text'][i] == "Biophysical":
                            text_near_checkboxes.append("Profile")
                        elif data['text'][i] == "OBS":
                            text_near_checkboxes.append(" -Limited (Biometry, Placenta, Position, Heart-rate)")    
                        elif data['text'][i] == "Breast":
                            text_near_checkboxes.append("Biopsy")
                        elif data['text'][i] == "Thyroid":
                            text_near_checkboxes.append("Biopsy")
                        elif data['text'][i] == "Temporal":
                            text_near_checkboxes.append("Artery Doppler")
                        elif data['text'][i] == "ABI":
                            text_near_checkboxes.append("Ankle Brachial index only")
                        elif data['text'][i] == "Lower":
                            text_near_checkboxes.append("Extremity Duplex with ABI")
                        elif data['text'][i] == "Upper":
                            text_near_checkboxes.append("Extremity Duplex")
                                
                        else:
                            text_near_checkboxes.append(data['text'][i])

                    
    for text, regions in checkbox_regions.items():
        # If it's a primary checkbox like "Shoulder"
        if text in ["Shoulder", "Knee", "Elbow", "Hip", "Ankle", "Wrist", "Hand", "Foot","Plantar","Venous","Breast","Thyroid","FNA","Breast","Thyroid","FNA", ]:
            for region in regions:
                full_text = text  # Start with the primary checkbox text

                # Check for "R" or "L" in nearby checkboxes
                nearby_margin = 50  # Adjust based on your PDF layout
                for direction in ["R", "L"]:
                    for dir_region in checkbox_regions[direction]:
                        if (region[0] - nearby_margin < dir_region[0] < region[0] + nearby_margin) and \
                           (region[1] - nearby_margin < dir_region[1] < region[1] + nearby_margin):
                            full_text += f" {direction}"  # Append direction to the text

                # Check for "Include X-Ray" in nearby checkboxes
                for xray_region in checkbox_regions["Include X-Ray"]:
                    if (region[0] - nearby_margin < xray_region[0] < region[0] + nearby_margin) and \
                       (region[1] - nearby_margin < xray_region[1] < region[1] + nearby_margin):
                        full_text += " with X-Ray"  # Append "with X-Ray" to the text

                # Append the constructed text to the results
                text_near_checkboxes.append(full_text)

        else:
            # For all other checkboxes, just add them directly
            text_near_checkboxes.extend([text for _ in regions])  # Use the text as many times as there are regions

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

@app.route('/upload', methods=['POST'])
def upload_and_convert():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    filename = secure_filename(file.filename)
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, filename)
        file.save(pdf_path)
        
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        combined_text = ''
        all_checkbox_texts = []
        for image in images:
            open_cv_image = np.array(image)
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            checked_checkboxes = []
            for cnt in contours:
                if is_checkbox_checked(cnt, thresh):
                    x, y, w, h = cv2.boundingRect(cnt)
                    checked_checkboxes.append((x, y, w, h))

            data = pytesseract.image_to_data(image, output_type=Output.DICT)
            checkbox_texts = extract_text_near_checkbox(checked_checkboxes, data)
            all_checkbox_texts.extend(checkbox_texts)

            text = pytesseract.image_to_string(image)
            combined_text += text + "\n"

        info = extract_info_from_text(combined_text)
        hl7_message = create_hl7_message(info, all_checkbox_texts)

        response = Response(hl7_message, mimetype='text/plain')
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.hl7"
        return response

def create_hl7_message(info, checkbox_data):

    current_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # MSH
    hl7_message = "MSH|^~\&|EXARIS-S|PDI|322913|PUREFORM|{timestamp}||ORM^O01^ORM_O01|{control_id}||2.3|||AL||||\n".format(
        control_id=info.get('AHC/WCB#', '12586231'),
        timestamp=current_timestamp
    )
    # PID   
    hl7_message += "PID|1|000000000^^^AB|{patient_id}^^^PDI|^^^AB|{name}^^^^||{dob}|F|||{address}^^{city}^AB^T2H 0L8^CANADA||{phone}|||\n".format(
        patient_id=info.get('AHC/WCB#', ''),
        name=info.get('Name', ''),
        dob=info.get('Date of Birth', ''),
        address=info.get('Address', ''),
        city=info.get('City', ''),
        phone=info.get('Phone Number', '')
    )
    # PV1
    hl7_message += f"PV1||1|0|^^^{info.get('Referring Physician', '')}\n"
    # ORC
    hl7_message += "ORC|SC||{order_control_number}||CA||||{timestamp}|||\n".format(
        order_control_number=info.get('Order Control Number', ''),
        timestamp=current_timestamp
    )
    # OBR
    hl7_message += "OBR|||{placer_order_number}|{universal_service_id}|||{observation_date_time}|{observation_date_time}||||||||||{filler_order_number}|{placer_order_number}|{filler_order_number}|{ordering_provider}|{timestamp}||I||*CATCH UP SPOT BLOCK - DO NOT BOOK*|||\n".format(
        placer_order_number=info.get('Placer Order Number', ''),
        universal_service_id=info.get('Universal Service ID', ''),
        observation_date_time=info.get('Observation Date Time', ''),
        filler_order_number=info.get('Filler Order Number', ''),
        ordering_provider=info.get('Ordering Provider', ''),
        timestamp=info.get('Timestamp', '20240301160754')
    )
    # FT1
    hl7_message += "FT1||||||||||||||AHCIP^Alberta Healthcare Insurance Plan\n"
    # OBX (from checkbox data)
    for index, obs in enumerate(checkbox_data, start=1):
        hl7_message += f"OBX|{index}|TX|||{obs}\n"
    # ZDS
    hl7_message += "ZDS|1.3.6.1.4.1.11157.3.5056010048.20211004155403.936844351.0^CM^^DICOM\n"

    return hl7_message



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf']

if __name__ == '__main__':
    app.run(debug=True)