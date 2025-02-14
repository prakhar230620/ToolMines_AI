from PIL import Image
import os
import svglib.svglib
from reportlab.graphics import renderPM
import cairosvg  # For vector formats
import rawpy  # For RAW images
import numpy as np
from reportlab.graphics import renderPDF

class ImageConverter:
    def __init__(self):
        self.supported_formats = {
            # Raster formats
            'jpg': {'type': 'raster'},
            'jpeg': {'type': 'raster'},
            'png': {'type': 'raster'},
            'gif': {'type': 'raster'},
            'bmp': {'type': 'raster'},
            'tiff': {'type': 'raster'},
            'webp': {'type': 'raster'},
            'ico': {'type': 'raster'},
            'ppm': {'type': 'raster'},
            'tga': {'type': 'raster'},
            
            # Vector formats
            'svg': {'type': 'vector'},
            'eps': {'type': 'vector'},
            'pdf': {'type': 'vector'},
            
            # Raw formats
            'raw': {'type': 'raw'},
            'cr2': {'type': 'raw'},
            'nef': {'type': 'raw'},
            'arw': {'type': 'raw'}
        }
    
    def convert(self, input_path, output_path, progress_bar=None):
        try:
            input_format = input_path.split('.')[-1].lower()
            output_format = output_path.split('.')[-1].lower()
            
            if output_format not in self.supported_formats:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            if progress_bar:
                progress_bar.setValue(25)
            
            # Determine conversion type
            input_type = self.supported_formats[input_format]['type']
            output_type = self.supported_formats[output_format]['type']
            
            # Handle SVG conversions
            if input_format == 'svg':
                self._convert_svg(input_path, output_path, output_format)
            # Handle other vector formats
            elif input_type == 'vector' and input_format != 'svg':
                self._convert_vector(input_path, output_path, input_format, output_format)
            # Handle raw formats
            elif input_type == 'raw':
                self._convert_raw(input_path, output_path, input_format, output_format)
            # Handle raster formats
            else:
                self._convert_raster(input_path, output_path, input_format, output_format)
            
            if progress_bar:
                progress_bar.setValue(100)
                
        except Exception as e:
            raise Exception(f"Image conversion failed: {str(e)}")
    
    def _convert_svg(self, input_path, output_path, output_format):
        """Convert SVG using svglib and cairosvg"""
        try:
            if output_format in ['png', 'jpg', 'jpeg']:
                # Use cairosvg for better quality raster conversion
                cairosvg.svg2png(url=input_path, write_to=output_path) if output_format == 'png' else \
                cairosvg.svg2jpg(url=input_path, write_to=output_path)
            elif output_format == 'pdf':
                # For PDF output, use svglib with reportlab
                drawing = svglib.svglib.svg2rlg(input_path)
                renderPDF.drawToFile(drawing, output_path)
            else:
                # Use svglib for other formats
                drawing = svglib.svglib.svg2rlg(input_path)
                renderPM.drawToFile(drawing, output_path, fmt=output_format.upper())
        except Exception as e:
            raise Exception(f"SVG conversion failed: {str(e)}")
    
    def _convert_vector(self, input_path, output_path, input_format, output_format):
        """Convert vector formats using cairosvg"""
        try:
            # First convert to SVG if needed (for EPS/PDF)
            if input_format in ['eps', 'pdf']:
                # Use pdf2svg or eps2svg utilities via subprocess if needed
                # For now, we'll raise an error as this requires additional tools
                raise NotImplementedError(f"Direct {input_format} conversion not supported yet. Please convert to SVG first.")
            
            # Then convert from SVG to target format
            if output_format == 'png':
                cairosvg.svg2png(url=input_path, write_to=output_path)
            elif output_format in ['jpg', 'jpeg']:
                cairosvg.svg2jpg(url=input_path, write_to=output_path)
            elif output_format == 'pdf':
                cairosvg.svg2pdf(url=input_path, write_to=output_path)
            else:
                raise ValueError(f"Unsupported vector output format: {output_format}")
        except Exception as e:
            raise Exception(f"Vector conversion failed: {str(e)}")
    
    def _convert_raw(self, input_path, output_path, input_format, output_format):
        """Convert RAW formats using rawpy"""
        try:
            with rawpy.imread(input_path) as raw:
                # Convert RAW to RGB numpy array
                rgb = raw.postprocess()
                
                # Convert numpy array to PIL Image
                img = Image.fromarray(rgb)
                
                # Save with optimal settings
                if output_format.lower() in ['jpg', 'jpeg']:
                    img.save(output_path, quality=95, optimize=True)
                elif output_format.lower() == 'png':
                    img.save(output_path, optimize=True)
                elif output_format.lower() == 'webp':
                    img.save(output_path, quality=95, method=6)
                else:
                    img.save(output_path)
        except Exception as e:
            raise Exception(f"RAW conversion failed: {str(e)}")
    
    def _convert_raster(self, input_path, output_path, input_format, output_format):
        """Convert between raster formats using Pillow"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if saving as JPEG
                if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'LA']:
                    img = img.convert('RGB')
                
                # Save with optimal settings
                if output_format.lower() in ['jpg', 'jpeg']:
                    img.save(output_path, quality=95, optimize=True)
                elif output_format.lower() == 'png':
                    img.save(output_path, optimize=True)
                elif output_format.lower() == 'webp':
                    img.save(output_path, quality=95, method=6)
                else:
                    img.save(output_path)
        except Exception as e:
            raise Exception(f"Raster conversion failed: {str(e)}")