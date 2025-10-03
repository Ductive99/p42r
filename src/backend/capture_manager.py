"""
Capture Manager

Handles image, screenshot, and video capture operations.
"""

import os
import logging
from typing import Optional
import tempfile


class CaptureManager:
    """Manages capture operations for images and screenshots."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = tempfile.gettempdir()
    
    def capture_webcam_image(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture an image from the webcam.
        
        Args:
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to captured image file, or None if failed
        """
        try:
            import cv2
            
            if not filename:
                filename = os.path.join(self.temp_dir, 'p42r_webcam_capture.jpg')
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.logger.error("Could not open webcam for image capture")
                return None
            
            ret, frame = cap.read()
            if not ret:
                self.logger.error("Could not capture image from webcam")
                cap.release()
                return None
            
            cv2.imwrite(filename, frame)
            cap.release()
            
            self.logger.info(f"Webcam image captured: {filename}")
            return filename
            
        except ImportError:
            self.logger.error("OpenCV not available for webcam capture")
            return None
        except Exception as e:
            self.logger.error(f"Error capturing webcam image: {e}")
            return None
    
    def capture_screenshot(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture a screenshot of the current screen.
        
        Args:
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to screenshot file, or None if failed
        """
        try:
            if not filename:
                filename = os.path.join(self.temp_dir, 'p42r_screenshot.png')
            
            # Try different screenshot methods based on availability
            success = False
            
            # Method 1: PIL ImageGrab (works on most systems)
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                img.save(filename)
                success = True
                self.logger.info(f"Screenshot captured with PIL: {filename}")
            except ImportError:
                pass
            
            # Method 2: gnome-screenshot (Linux)
            if not success:
                try:
                    import subprocess
                    result = subprocess.run([
                        'gnome-screenshot', '-f', filename
                    ], capture_output=True, check=True)
                    success = True
                    self.logger.info(f"Screenshot captured with gnome-screenshot: {filename}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
            
            # Method 3: scrot (Linux)
            if not success:
                try:
                    import subprocess
                    result = subprocess.run([
                        'scrot', filename
                    ], capture_output=True, check=True)
                    success = True
                    self.logger.info(f"Screenshot captured with scrot: {filename}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
            
            if success and os.path.exists(filename):
                return filename
            else:
                self.logger.error("All screenshot methods failed")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary capture files.
        
        Args:
            max_age_hours: Maximum age of files to keep
            
        Returns:
            Number of files cleaned up
        """
        try:
            import time
            import glob
            
            pattern = os.path.join(self.temp_dir, 'p42r_*')
            files = glob.glob(pattern)
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0
            
            for file_path in files:
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleaned_count += 1
                        self.logger.debug(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Could not clean up file {file_path}: {e}")
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old capture files")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return 0
    
    def get_capture_info(self) -> dict:
        """Get information about capture capabilities."""
        info = {
            'webcam_available': False,
            'screenshot_methods': [],
            'temp_dir': self.temp_dir
        }
        
        # Check webcam availability
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                info['webcam_available'] = True
                cap.release()
        except ImportError:
            pass
        
        # Check screenshot methods
        try:
            from PIL import ImageGrab
            info['screenshot_methods'].append('PIL')
        except ImportError:
            pass
        
        try:
            import subprocess
            subprocess.run(['gnome-screenshot', '--version'], 
                         capture_output=True, check=True)
            info['screenshot_methods'].append('gnome-screenshot')
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            import subprocess
            subprocess.run(['scrot', '--version'], 
                         capture_output=True, check=True)
            info['screenshot_methods'].append('scrot')
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return info
