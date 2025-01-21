from moviepy.editor import VideoFileClip
import ffmpeg
import os

class VideoConverter:
    def __init__(self):
        self.supported_formats = {
            # Common formats
            'mp4': {
                'type': 'common',
                'video_codec': 'libx264',
                'audio_codec': 'aac',
                'container': 'mp4'
            },
            'avi': {
                'type': 'common',
                'video_codec': 'mpeg4',
                'audio_codec': 'mp3',
                'container': 'avi'
            },
            'mkv': {
                'type': 'common',
                'video_codec': 'libx264',
                'audio_codec': 'aac',
                'container': 'matroska'
            },
            'mov': {
                'type': 'common',
                'video_codec': 'libx264',
                'audio_codec': 'aac',
                'container': 'mov'
            },
            
            # Web formats
            'webm': {
                'type': 'web',
                'video_codec': 'libvpx-vp9',
                'audio_codec': 'libopus',
                'container': 'webm'
            },
            'ogv': {
                'type': 'web',
                'video_codec': 'libtheora',
                'audio_codec': 'libvorbis',
                'container': 'ogg'
            },
            
            # Professional formats
            'mxf': {
                'type': 'professional',
                'video_codec': 'mpeg2video',
                'audio_codec': 'pcm_s16le',
                'container': 'mxf'
            },
            'dv': {
                'type': 'professional',
                'video_codec': 'dvvideo',
                'audio_codec': 'pcm_s16le',
                'container': 'dv'
            },
            
            # Mobile formats
            '3gp': {
                'type': 'mobile',
                'video_codec': 'h263',
                'audio_codec': 'aac',
                'container': '3gp'
            },
            'm4v': {
                'type': 'mobile',
                'video_codec': 'libx264',
                'audio_codec': 'aac',
                'container': 'm4v'
            }
        }
    
    def convert(self, input_path, output_path, progress_bar=None):
        try:
            output_format = output_path.split('.')[-1].lower()
            
            if output_format not in self.supported_formats:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            if progress_bar:
                progress_bar.setValue(25)
            
            # Use FFmpeg for conversion
            self._convert_with_ffmpeg(input_path, output_path, output_format)
            
            if progress_bar:
                progress_bar.setValue(100)
                
        except Exception as e:
            raise Exception(f"Video conversion failed: {str(e)}")
    
    def _convert_with_ffmpeg(self, input_path, output_path, output_format):
        try:
            # Get format settings
            format_settings = self.supported_formats[output_format]
            
            # Build FFmpeg command
            stream = ffmpeg.input(input_path)
            
            # Apply format-specific settings
            stream = ffmpeg.output(stream, output_path,
                                 **self._get_format_settings(format_settings))
            
            # Run the conversion
            ffmpeg.run(stream, overwrite_output=True)
            
        except Exception as e:
            raise Exception(f"FFmpeg conversion failed: {str(e)}")
    
    def _get_format_settings(self, format_settings):
        settings = {
            'vcodec': format_settings['video_codec'],
            'acodec': format_settings['audio_codec']
        }
        
        # Add format-specific settings
        if format_settings['type'] == 'common':
            if format_settings['video_codec'] == 'libx264':
                settings.update({
                    'preset': 'medium',
                    'crf': '23',
                    'movflags': '+faststart'
                })
        
        elif format_settings['type'] == 'web':
            if format_settings['video_codec'] == 'libvpx-vp9':
                settings.update({
                    'b:v': '1M',
                    'deadline': 'good',
                    'cpu-used': '2'
                })
        
        elif format_settings['type'] == 'professional':
            settings.update({
                'b:v': '50M',
                'maxrate': '50M',
                'bufsize': '50M'
            })
        
        elif format_settings['type'] == 'mobile':
            settings.update({
                'b:v': '500k',
                'b:a': '128k',
                'ar': '44100'
            })
        
        return settings
