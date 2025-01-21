# Universal File Converter

A powerful desktop application that allows you to convert files between different formats locally on your device.

## Features

- Convert various file types:
  - Images (PNG, JPEG, BMP, GIF)
  - Documents (PDF, DOCX, TXT)
  - Audio (MP3, WAV, OGG)
  - Video (MP4, AVI, MKV)
- Local conversion for files under 100MB
- Modern and user-friendly interface
- Progress tracking for conversions
- File size validation

## Installation

1. Install Python 3.8 or higher
2. Install ImageMagick: https://imagemagick.org/script/download.php#windows  
3. Install ffmpeg in your os and add on path on environment variable
4. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Select a file using the "Select File" button
3. Choose the desired output format from the dropdown menu
4. Click "Convert" to start the conversion
5. Select where to save the converted file

## Limitations

- Maximum file size: 100MB
- Supported formats are limited to those listed above
- Some document conversions (PDF to DOCX, DOCX to PDF) are not yet implemented

## Future Features

- Cloud storage support for files over 100MB
- Premium subscription for advanced features
- Additional file format support
- Batch conversion capability
