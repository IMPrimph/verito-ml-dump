from flask import Flask, request, jsonify
import requests
from pymediainfo import MediaInfo
from PIL import Image
from io import BytesIO
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvalidAPIUsage(Exception):
    pass

@app.route('/asset_metadata', methods=['POST'])
def get_metadata():
    data = request.json
    url = data.get('url')
    asset_type = data.get('type')

    if not url or not asset_type:
        return jsonify({'error': 'URL and asset_type are required'}), 400

    try:
        metadata = handle(url, asset_type)
        return jsonify(metadata)
    except InvalidAPIUsage as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(e)
        return jsonify({'error': 'Something went wrong!'}), 500

def handle(url: str, asset_type: str):
    """
    Args:
        url (str): URL of the video or image for which metadata is to be given
    Returns:
        dict: Metadata of the asset
    Raises:
        InvalidAPIUsage
    """
    try:
        return get_asset_metadata(url, asset_type)
    except Exception as e:
        print(e)
        raise InvalidAPIUsage('Something went wrong!')

def get_asset_metadata(asset_url, asset_type):
    """
    Get the metadata of an asset

    Args:
        asset_url(str): URL to the asset
        asset_type(str): Type of asset - video or image

    Returns:
        dict: Metadata containing duration (if video) and dimension
    """
    metadata = {}
    if asset_type == 'video':
        try:
            metadata = get_video_metadata(asset_url)
        except Exception as e:
            print(e)
            try:
                metadata = get_video_metadata_full_download(asset_url)
            except Exception as ex:
                print(ex)
                raise InvalidAPIUsage('Failed to get video metadata')
        return metadata
    elif asset_type == 'image':
        try:
            metadata = get_image_metadata(asset_url)
        except Exception as e:
            print(e)
            raise InvalidAPIUsage('Failed to get image metadata')
        return metadata
    else:
        return metadata

def get_video_metadata(video_url):
    """
    Get the metadata of a video from its URL using pymediainfo with range requests

    Args:
        video_url (str): URL of the video

    Returns:
        dict: Metadata containing duration and dimension
    """
    try:
        # Attempting a range request
        headers = {'Range': 'bytes=0-5000000'}  # Increase range as needed
        response = requests.get(video_url, headers=headers, stream=True)
        if response.status_code not in (200, 206):
            logger.info('Range request not supported, attempting full download')
            raise InvalidAPIUsage('Range request not supported')

        # Load the streamed response content into a BytesIO object
        temp_file = BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # Filter out keep-alive new chunks
                temp_file.write(chunk)

        # Reset the file pointer to the beginning
        temp_file.seek(0)

        # Use pymediainfo to parse the partial file
        media_info = MediaInfo.parse(temp_file)

        # Extract metadata from the video stream
        for track in media_info.tracks:
            if track.track_type == "Video":
                metadata = {
                    'duration': track.duration / 1000,  # Convert from ms to seconds
                    'dimension': f"{track.width}x{track.height}"
                }
                return metadata

        logger.error('No video stream found in the provided range.')
        raise InvalidAPIUsage('No video stream found')
    except Exception as e:
        print(e)
        raise InvalidAPIUsage('Failed to get video metadata with range request')

def get_video_metadata_full_download(video_url):
    """
    Fallback: Get the metadata of a video by downloading the full file

    Args:
        video_url (str): URL of the video

    Returns:
        dict: Metadata containing duration and dimension
    """
    try:
        print('full video download')
        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            raise FileNotFoundError(f'File {video_url} not found')

        temp_file = BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)

        temp_file.seek(0)

        media_info = MediaInfo.parse(temp_file)

        for track in media_info.tracks:
            if track.track_type == "Video":
                metadata = {
                    'duration': track.duration / 1000,  # Convert from ms to seconds
                    'dimension': f"{track.width}x{track.height}"
                }
                return metadata

        raise InvalidAPIUsage('No video stream found after full download')
    except Exception as e:
        print(e)
        raise InvalidAPIUsage('Failed to get video metadata after full download')

def get_image_metadata(image_url):
    """
    Get the metadata of an image from its URL

    Args:
        image_url (str): URL of the image

    Returns:
        dict: Metadata containing dimension
    """
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code != 200:
            raise FileNotFoundError(f'File {image_url} not found')

        image = Image.open(BytesIO(response.content))
        width, height = image.width, image.height
        return {
            'dimension': f'{width}x{height}'
        }
    except Exception as e:
        print(e)
        raise InvalidAPIUsage('Failed to get image metadata')

if __name__ == '__main__':
    app.run(port=5000)
