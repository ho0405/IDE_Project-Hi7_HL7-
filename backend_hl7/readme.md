Backend Installation Guide
This guide will walk you through the installation process for setting up the backend environment required to run the application.

# Step 1: Installing Dependencies
## 1.1 Poppler
1. Download the Poppler package (version 24.02.0) from folder
2. Extract the downloaded package. or From the step 1 folder.
3. Copy the extracted poppler-24.02.0 folder.
4. Paste the copied folder into C:\Program Files.

## 1.2 Tesseract OCR
1. Download the Tesseract OCR installer (version 5.0.1.20220118) from the official website: Tesseract OCR Releases. or from the Step 1 folder
2. Run the downloaded installer (tesseract-ocr-w64-setup-v5.0.1.20220118.exe).
3. Follow the installation instructions provided by the installer.
4. During installation, specify the installation directory as the same folder where you pasted the Poppler folder in Step 1.1.

# Step 2: Configuring Environment Variables
1. Add the paths of the Poppler and Tesseract binaries to the system's PATH environment variable:

For Poppler: C:\Program Files\poppler-24.02.0\Library\bin

For Tesseract: The installation directory you specified during installation.

# Step 3: Running the Backend
1. Clone or download the backend source code from the repository.
2. Navigate to the backend directory.
3. Install the required Python packages by running:
4. Copy code
python -m pip install -r requirements.txt
5. Start the Flask application by running:
Copy code
python app.py
6. Once the application is running, you can interact with it using the provided endpoints.


# Test
1. Navigate to the website https://frontend-hl7.vercel.app/.
2. Sign up for an account if you haven't already.
3. Sign in to your account.
4. Test the PDF file upload functionality using the provided test cases located in the Test_cases folder.
5. Upload the PDF files and observe the behavior of the backend application.
6. Verify that the HL7 messages are generated correctly based on the extracted information from the uploaded PDF files.