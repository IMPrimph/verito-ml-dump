from pytube import YouTube
from moviepy import VideoFileClip
import re
import os
from datetime import datetime
from typing import Tuple, Optional
import logging

class YouTubeClipperError(Exception):
    """Base exception class for YouTubeClipper"""
    pass

class InvalidTimestampError(YouTubeClipperError):
    """Raised when timestamp format is invalid"""
    pass

class TimestampOutOfRangeError(YouTubeClipperError):
    """Raised when timestamp is outside video duration"""
    pass

class PrivateVideoError(YouTubeClipperError):
    """Raised when video is private or unavailable"""
    pass

class VideoUnavailableError(YouTubeClipperError):
    """Raised when video metadata cannot be retrieved"""
    pass

class YouTubeClipper:
    def __init__(self, output_dir: str = "downloads"):
        """
        Initialize YouTubeClipper with output directory
        
        Args:
            output_dir (str): Directory to save downloaded clips
        """
        self.output_dir = output_dir
        self._setup_logging()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('youtube_clipper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _parse_timestamp(self, timestamp: str) -> int:
        """
        Convert timestamp string to seconds
        
        Args:
            timestamp (str): Timestamp in format HH:MM:SS or MM:SS
            
        Returns:
            int: Time in seconds
            
        Raises:
            InvalidTimestampError: If timestamp format is invalid
        """
        try:
            # Try parsing as HH:MM:SS
            time_formats = ["%H:%M:%S", "%M:%S"]
            
            for fmt in time_formats:
                try:
                    time_obj = datetime.strptime(timestamp, fmt)
                    total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
                    return total_seconds
                except ValueError:
                    continue
                    
            raise InvalidTimestampError(f"Invalid timestamp format: {timestamp}. Use HH:MM:SS or MM:SS")
            
        except Exception as e:
            raise InvalidTimestampError(f"Error parsing timestamp: {str(e)}")
    
    def _validate_timestamps(self, video_length: int, start_time: int, end_time: int):
        """
        Validate that timestamps are within video duration
        
        Args:
            video_length (int): Total video duration in seconds
            start_time (int): Start time in seconds
            end_time (int): End time in seconds
            
        Raises:
            TimestampOutOfRangeError: If timestamps are invalid or out of range
        """
        if start_time >= end_time:
            raise TimestampOutOfRangeError("Start time must be less than end time")
            
        if start_time < 0 or end_time > video_length:
            raise TimestampOutOfRangeError(
                f"Timestamps must be between 0 and video length ({video_length} seconds)"
            )
    
    def _get_video_info(self, video_url: str) -> YouTube:
        """
        Get YouTube video information with error handling
        
        Args:
            video_url (str): YouTube video URL
            
        Returns:
            YouTube: YouTube object
            
        Raises:
            PrivateVideoError: If video is private
            VideoUnavailableError: If video metadata cannot be retrieved
        """
        try:
            yt = YouTube(video_url)
            
            # Wait for video metadata to load
            tries = 0
            while tries < 3:
                try:
                    # Check if video length is available
                    if yt.length is None:
                        raise VideoUnavailableError("Could not retrieve video length")
                    
                    # Check if video is private or unavailable
                    if not yt.watch_html:
                        raise PrivateVideoError("This video is private or unavailable")
                    
                    return yt
                except Exception as e:
                    tries += 1
                    if tries == 3:
                        raise VideoUnavailableError(f"Failed to retrieve video information after {tries} attempts")
                    self.logger.warning(f"Attempt {tries}: Failed to get video info, retrying...")
            
        except Exception as e:
            raise VideoUnavailableError(f"Error accessing video: {str(e)}")

    def download_clip(self, video_url: str, start_time: str, end_time: str) -> str:
        """
        Download a clip from a YouTube video
        
        Args:
            video_url (str): YouTube video URL
            start_time (str): Start timestamp (HH:MM:SS or MM:SS)
            end_time (str): End timestamp (HH:MM:SS or MM:SS)
            
        Returns:
            str: Path to the downloaded clip
            
        Raises:
            PrivateVideoError: If video is private or unavailable
            YouTubeClipperError: For other download-related errors
        """
        temp_path = None
        video = None
        video_clip = None
        
        try:
            # Get video information
            self.logger.info(f"Attempting to access video: {video_url}")
            yt = self._get_video_info(video_url)
            
            # Convert timestamps to seconds
            start_seconds = self._parse_timestamp(start_time)
            end_seconds = self._parse_timestamp(end_time)
            
            # Validate timestamps
            self._validate_timestamps(yt.length, start_seconds, end_seconds)
            
            # Download the full video
            self.logger.info("Downloading video...")
            video_stream = yt.streams.get_highest_resolution()
            if not video_stream:
                raise YouTubeClipperError("No suitable video stream found")
                
            temp_path = video_stream.download(
                output_path=self.output_dir,
                filename=f"temp_{yt.video_id}.mp4"
            )
            
            # Create clip
            self.logger.info("Creating clip...")
            video = VideoFileClip(temp_path)
            video_clip = video.subclip(start_seconds, end_seconds)
            
            # Save clip
            output_path = os.path.join(
                self.output_dir,
                f"{yt.title}_{start_time}_{end_time}.mp4"
            )
            video_clip.write_videofile(output_path)
            
            self.logger.info(f"Clip saved successfully: {output_path}")
            return output_path
            
        except (PrivateVideoError, InvalidTimestampError, TimestampOutOfRangeError, VideoUnavailableError):
            raise
        except Exception as e:
            raise YouTubeClipperError(f"Error downloading clip: {str(e)}")
        finally:
            # Clean up resources
            try:
                if video_clip:
                    video_clip.close()
                if video:
                    video.close()
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                self.logger.error(f"Error during cleanup: {str(e)}")

clipper = YouTubeClipper(output_dir="my_clips")

# Download a clip
try:
    output_path = clipper.download_clip(
        video_url="https://www.youtube.com/watch?v=qGAPokt6Buo",
        start_time="00:30",
        end_time="01:45"
    )
    print(f"Clip saved to: {output_path}")
except PrivateVideoError:
    print("Video is private or unavailable")
except InvalidTimestampError as e:
    print(f"Invalid timestamp: {str(e)}")
except TimestampOutOfRangeError as e:
    print(f"Timestamp out of range: {str(e)}")
except YouTubeClipperError as e:
    print(f"Error: {str(e)}")