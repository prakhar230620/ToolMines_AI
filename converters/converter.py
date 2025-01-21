from flask import Blueprint, request, jsonify, send_file, render_template, after_this_request, session
from werkzeug.utils import secure_filename
import os
import tempfile
from threading import Thread
import time
import shutil
from converters import ImageConverter, DocumentConverter, AudioConverter, VideoConverter
import atexit

converter_bp = Blueprint('converter', __name__)

# Initialize converters
image_converter = ImageConverter()
document_converter = DocumentConverter()
audio_converter = AudioConverter()
video_converter = VideoConverter()

# Store active conversions and uploaded files
active_conversions = {}
uploaded_files = {}
temp_dir = os.path.join(tempfile.gettempdir(), 'converter')

# Create temp directory if it doesn't exist
os.makedirs(temp_dir, exist_ok=True)

# Cleanup temp directory on application exit
def cleanup_temp_dir():
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up temp directory: {e}")

atexit.register(cleanup_temp_dir)

FORMAT_TYPES = {
    'image': {
        'Raster Formats': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'ico'],
        'Vector Formats': ['svg', 'eps', 'pdf'],
        'Raw Formats': ['raw', 'cr2', 'nef', 'arw']
    },
    'document': {
        'Text Documents': ['txt', 'docx', 'doc', 'rtf', 'odt', 'pdf'],
        'Markup': ['md', 'html', 'xml'],
        'Spreadsheets': ['xlsx', 'xls', 'csv', 'ods'],
        'Presentations': ['pptx', 'ppt', 'odp'],
        'eBooks': ['epub', 'mobi', 'azw3'],
        'Data Formats': ['json', 'yaml', 'xml']
    },
    'audio': {
        'Lossy Formats': ['mp3', 'aac', 'ogg', 'm4a', 'wma'],
        'Lossless Formats': ['wav', 'flac', 'alac', 'aiff'],
        'Professional Formats': ['pcm', 'dsd']
    },
    'video': {
        'Common Formats': ['mp4', 'avi', 'mkv', 'mov', 'wmv'],
        'Web Formats': ['webm', 'ogv'],
        'Professional Formats': ['mxf', 'dv'],
        'Mobile Formats': ['3gp', 'm4v']
    }
}

def get_converter(format_type):
    converters = {
        'image': image_converter,
        'document': document_converter,
        'audio': audio_converter,
        'video': video_converter
    }
    return converters.get(format_type.lower())

def get_format_type(file_extension):
    file_extension = file_extension.lower()
    for format_type, categories in FORMAT_TYPES.items():
        for category, formats in categories.items():
            if file_extension in formats:
                return format_type
    return None

def setup_converter_routes(app, socketio, auth_required=None, track_tool_usage=None):
    """Set up routes for the converter with authentication and usage tracking"""
    
    @app.route('/converter')
    @auth_required if auth_required else lambda f: f
    def converter():
        if track_tool_usage:
            track_tool_usage('CONV001', session.get('user_id'))
        return render_template('converter/converter.html', format_types=FORMAT_TYPES)

    @app.route('/get_formats', methods=['GET'])
    def get_formats():
        return jsonify(FORMAT_TYPES)

    @app.route('/convert', methods=['POST'])
    @auth_required if auth_required else lambda f: f
    def convert_file():
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        input_extension = file.filename.rsplit('.', 1)[1].lower()
        output_format = request.form.get('output_format', '').lower()
        
        # Determine format type
        format_type = get_format_type(input_extension)
        if not format_type:
            return jsonify({'error': f'Unsupported input format: {input_extension}'}), 400
            
        # Get appropriate converter
        converter = get_converter(format_type)
        if not converter:
            return jsonify({'error': 'Converter not found'}), 500
        
        # Save uploaded file
        input_filename = secure_filename(file.filename)
        input_path = os.path.join(temp_dir, input_filename)
        file.save(input_path)
        
        # Generate output path
        output_filename = f"converted_{os.path.splitext(input_filename)[0]}.{output_format}"
        output_path = os.path.join(temp_dir, output_filename)

        try:
            # Convert file
            converter.convert(input_path, output_path)
            
            # Store file paths for later cleanup
            file_id = str(time.time())
            uploaded_files[file_id] = {
                'input_path': input_path,
                'output_path': output_path
            }
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'message': 'File converted successfully'
            })
        except Exception as e:
            # Cleanup input file
            if os.path.exists(input_path):
                os.remove(input_path)
            return jsonify({'error': str(e)}), 500

    @app.route('/download/<file_id>', methods=['GET'])
    def download_file(file_id):
        if file_id not in uploaded_files:
            return jsonify({'error': 'File not found'}), 404
            
        file_paths = uploaded_files[file_id]
        output_path = file_paths['output_path']
        
        if not os.path.exists(output_path):
            return jsonify({'error': 'File not found'}), 404

        # Schedule cleanup after request is complete
        @after_this_request
        def remove_file(response):
            try:
                cleanup_files(file_id)
            except Exception as e:
                print(f"Error during file cleanup: {e}")
            return response
            
        try:
            return send_file(
                output_path,
                as_attachment=True,
                download_name=os.path.basename(output_path)
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def cleanup_files(file_id):
        if file_id in uploaded_files:
            paths = uploaded_files[file_id]
            for path in paths.values():
                try:
                    if os.path.exists(path):
                        # Add a small delay to ensure file is not in use
                        time.sleep(0.1)
                        os.remove(path)
                except Exception as e:
                    print(f"Error removing file {path}: {e}")
            del uploaded_files[file_id]

    # Register blueprint
    app.register_blueprint(converter_bp, url_prefix='/converter')
