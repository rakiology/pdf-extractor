from flask import Flask, request, send_from_directory, jsonify, render_template_string
import os
from werkzeug.utils import secure_filename
from main import extract_signatures_from_pdf, extract_base64_images_from_svg, extract_all_from_pdf

UPLOAD_FOLDER = 'uploads'
SIGNATURES_FOLDER = 'extracted_signatures'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SIGNATURES_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Extract all data (images and text)
            all_data = extract_all_from_pdf(filepath)
            return jsonify(all_data)
        return jsonify({'error': 'Invalid file type'}), 400
    # Serve the HTML directly from the backend for GET
    with open('index.html', encoding='utf-8') as f:
        return f.read()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Extract all data (images and text)
        all_data = extract_all_from_pdf(filepath)
        return jsonify(all_data)
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/signatures/<filename>')
def get_signature(filename):
    return send_from_directory(SIGNATURES_FOLDER, filename)

@app.route('/list_signatures')
def list_signatures():
    files = [f for f in os.listdir(SIGNATURES_FOLDER) if f.endswith('.png')]
    return jsonify({'images': ['/signatures/' + f for f in files]})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))  # fallback to 10000 if not on Render
    app.run(host="0.0.0.0", port=port, debug=True)

