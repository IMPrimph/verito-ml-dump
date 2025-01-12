from flask import Flask, request, jsonify
import requests
from pymediainfo import MediaInfo
from PIL import Image
from io import BytesIO
import logging
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor()

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
        if asset_type == 'video':
            future = executor.submit(handle_video_metadata, url)
            metadata = future.result()
        elif asset_type == 'image':
            metadata = handle_image_metadata(url)
        else:
            return jsonify({'error': 'Unsupported asset type'}), 400

        return jsonify(metadata)
    except InvalidAPIUsage as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(e)
        return jsonify({'error': 'Something went wrong!'}), 500

def handle_video_metadata(url: str):
    try:
        return get_video_metadata(url)
    except Exception as e:
        logger.error(e)
        raise InvalidAPIUsage('Something went wrong with video processing!')

def handle_image_metadata(url: str):
    try:
        return get_image_metadata(url)
    except Exception as e:
        logger.error(e)
        raise InvalidAPIUsage('Something went wrong with image processing!')

def get_video_metadata(video_url):
    try:
        headers = {'Range': 'bytes=0-5000000'}
        response = requests.get(video_url, headers=headers, stream=True)
        if response.status_code not in (200, 206):
            logger.info('Range request not supported, attempting full download')
            raise InvalidAPIUsage('Range request not supported')

        temp_file = BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)

        temp_file.seek(0)
        return parse_video_metadata(temp_file)
    except Exception as e:
        logger.error(e)
        raise InvalidAPIUsage('Failed to get video metadata with range request')

def parse_video_metadata(temp_file):
    media_info = MediaInfo.parse(temp_file)
    for track in media_info.tracks:
        if track.track_type == "Video":
            return {
                'duration': track.duration / 1000,
                'dimension': f"{track.width}x{track.height}"
            }
    raise InvalidAPIUsage('No video stream found')

def get_image_metadata(image_url):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code != 200:
            raise FileNotFoundError(f'File {image_url} not found')

        image = Image.open(BytesIO(response.content))
        width, height = image.width, image.height
        return {'dimension': f'{width}x{height}'}
    except Exception as e:
        logger.error(e)
        raise InvalidAPIUsage('Failed to get image metadata')

if __name__ == '__main__':
    app.run(port=5000)
