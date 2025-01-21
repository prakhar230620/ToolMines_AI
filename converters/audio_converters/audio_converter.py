from pydub import AudioSegment
import os
import ffmpeg

class AudioConverter:
    def __init__(self):
        self.supported_formats = {
            # Lossy formats
            'mp3': {
                'type': 'lossy',
                'codec': 'libmp3lame',
                'default_bitrate': '192k'
            },
            'aac': {
                'type': 'lossy',
                'codec': 'aac',
                'default_bitrate': '192k'
            },
            'ogg': {
                'type': 'lossy',
                'codec': 'libvorbis',
                'default_bitrate': '192k'
            },
            'm4a': {
                'type': 'lossy',
                'codec': 'aac',
                'default_bitrate': '192k'
            },
            'wma': {
                'type': 'lossy',
                'codec': 'wmav2',
                'default_bitrate': '192k'
            },
            
            # Lossless formats
            'wav': {
                'type': 'lossless',
                'codec': 'pcm_s16le'
            },
            'flac': {
                'type': 'lossless',
                'codec': 'flac'
            },
            'alac': {
                'type': 'lossless',
                'codec': 'alac'
            },
            'aiff': {
                'type': 'lossless',
                'codec': 'pcm_s16be'
            },
            
            # Professional formats
            'pcm': {
                'type': 'professional',
                'codec': 'pcm_s24le'
            },
            'dsd': {
                'type': 'professional',
                'codec': 'dsd'
            }
        }
    
    def convert(self, input_path, output_path, progress_bar=None):
        try:
            input_format = input_path.split('.')[-1].lower()
            output_format = output_path.split('.')[-1].lower()
            
            if output_format not in self.supported_formats:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            if progress_bar:
                progress_bar.setValue(25)
            
            # Determine conversion method based on format types
            input_type = self.supported_formats[input_format]['type']
            output_type = self.supported_formats[output_format]['type']
            
            if self._requires_ffmpeg(input_format, output_format):
                self._convert_with_ffmpeg(input_path, output_path, input_format, output_format)
            else:
                self._convert_with_pydub(input_path, output_path, input_format, output_format)
            
            if progress_bar:
                progress_bar.setValue(100)
                
        except Exception as e:
            raise Exception(f"Audio conversion failed: {str(e)}")
    
    def _requires_ffmpeg(self, input_format, output_format):
        # Use FFmpeg for professional formats or specific codec requirements
        return (self.supported_formats[input_format]['type'] == 'professional' or
                self.supported_formats[output_format]['type'] == 'professional')
    
    def _convert_with_pydub(self, input_path, output_path, input_format, output_format):
        try:
            # Load the audio file
            audio = AudioSegment.from_file(input_path, format=input_format)
            
            # Apply format-specific settings
            export_params = self._get_export_params(output_format)
            
            # Export with parameters
            audio.export(output_path, format=output_format, **export_params)
            
        except Exception as e:
            raise Exception(f"Pydub conversion failed: {str(e)}")
    
    def _convert_with_ffmpeg(self, input_path, output_path, input_format, output_format):
        try:
            # Get format settings
            format_settings = self.supported_formats[output_format]
            
            # Build FFmpeg command
            stream = ffmpeg.input(input_path)
            
            # Apply codec and format-specific settings
            stream = ffmpeg.output(stream, output_path,
                                 acodec=format_settings['codec'],
                                 **self._get_ffmpeg_params(output_format))
            
            # Run the conversion
            ffmpeg.run(stream, overwrite_output=True)
            
        except Exception as e:
            raise Exception(f"FFmpeg conversion failed: {str(e)}")
    
    def _get_export_params(self, format):
        format_settings = self.supported_formats[format]
        params = {}
        
        if format_settings['type'] == 'lossy':
            params['bitrate'] = format_settings['default_bitrate']
            
        if format == 'mp3':
            params.update({
                'codec': 'libmp3lame',
                'parameters': ['-q:a', '0']
            })
        elif format == 'ogg':
            params.update({
                'codec': 'libvorbis',
                'parameters': ['-q:a', '6']
            })
        elif format == 'wav':
            params.update({
                'parameters': ['-acodec', 'pcm_s16le']
            })
        elif format == 'flac':
            params.update({
                'parameters': ['-compression_level', '8']
            })
            
        return params
    
    def _get_ffmpeg_params(self, format):
        params = {}
        format_settings = self.supported_formats[format]
        
        if format_settings['type'] == 'lossy':
            params['b:a'] = format_settings['default_bitrate']
            
        if format == 'flac':
            params['compression_level'] = '8'
        elif format == 'wav':
            params['sample_fmt'] = 's16'
        elif format == 'dsd':
            params.update({
                'sample_rate': '2822400',
                'sample_fmt': 'dsd'
            })
            
        return params
