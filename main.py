import requests
from pymediainfo import MediaInfo
from PIL import Image
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvalidAPIUsage(Exception):
    pass

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
            # metadata = get_video_metadata(asset_url)
            metadata = get_video_metadata_full_download(asset_url)
        except Exception as e:
            print(e)
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
        headers = {'Range': 'bytes=0-2000000'}  # Adjust range as needed
        response = requests.get(video_url, headers=headers, stream=True)
        # if response.status_code not in (200, 206):
        #     raise FileNotFoundError(f'File {video_url} not found or range not supported')
        if response.status_code not in (200, 206):
            logger.info('Range request not supported, attempting full download')
            response = requests.get(video_url)
            if response.status_code != 200:
                raise FileNotFoundError(f'File {video_url} not found')

        # temp_file = BytesIO(response.content)
        # Load the streamed response content into a BytesIO object
        temp_file = BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # Filter out keep-alive new chunks
                temp_file.write(chunk)

        # Reset the file pointer to the beginning
        temp_file.seek(0)
        media_info = MediaInfo.parse(temp_file)

        for track in media_info.tracks:
            if track.track_type == "Video":
                print(track, response)
                metadata = {
                    'duration': track.duration / 1000,  # Convert from ms to seconds
                    'dimension': f"{track.width}x{track.height}"
                }
                return metadata
        raise InvalidAPIUsage('No video stream found')
    except Exception as e:
        print(e)
        raise InvalidAPIUsage('Failed to get video metadata')

def get_video_metadata_full_download(video_url):
    """
    Fallback: Get the metadata of a video by downloading the full file

    Args:
        video_url (str): URL of the video

    Returns:
        dict: Metadata containing duration and dimension
    """
    try:
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

# Example usage
# print(handle("https://example.com/video.mp4", "video"))
# print(handle("https://example.com/image.jpg", "image"))

arr = [
  "https://adint-assets.datamagic.rocks/e/ed/ed6/ed69/ed69e/ed69eb/ed69eb76-788d-4456-872c-3c513dede1d1/1806c77b-fe95-469c-9aaa-9917053bc253.mp4", 
  "https://adint-assets.datamagic.rocks/c/c7/c79/c790/c790d/c790dc/c790dcf6-c79a-4358-b1e6-d67d48bf2b4f/5314df2f-f30a-48a6-8dfb-237872164093", 
  "https://adint-assets.datamagic.rocks/f/f1/f1c/f1c2/f1c23/f1c233/f1c23308-1555-4d08-80bb-eb03db3194eb/b36f65eb-3478-4d85-bd81-ff73eefa9976.mp4", 
  "https://adint-assets.datamagic.rocks/9/98/982/9821/98217/982174/9821741e-50b5-4117-9c45-77fc099d14dc/d6600b33-d72f-4587-ac50-921c7ac328fe.mp4", 
  "https://adint-assets.datamagic.rocks/6/6c/6c0/6c0f/6c0f0/6c0f0a/6c0f0a28-b75b-49ac-a2a5-525d9ee3c405/ae15a732-071c-4c02-bc70-e53fd0068009.mp4", 
  "https://adint-assets.datamagic.rocks/3/36/360/3609/36093/36093e/36093ef8-c2f6-46d1-a17a-970c7783efa7/0c1476de-43cb-478f-b464-cc1792e97d25", 
  "https://adint-assets.datamagic.rocks/c/cc/cce/cce1/cce1f/cce1fe/cce1fee0-1058-4bf7-bfe2-065fc1f75817/ea6e650d-3f62-442b-9cbe-779a56399d39", 
  "https://adint-assets.datamagic.rocks/6/65/65d/65d7/65d7f/65d7f9/65d7f968-a232-4eec-9d54-c3e4f5745125/6c2d3104-b5f3-4792-a050-c95fc890ad4d",  
  "https://adint-assets.datamagic.rocks/c/ca/ca6/ca62/ca626/ca6265/ca626593-4378-4547-9edd-c1afbf97fa80/40696ae6-dc71-43e0-9060-2cd998e06808",  
  "https://adint-assets.datamagic.rocks/e/ec/ec5/ec51/ec510/ec5105/ec510594-c535-42b6-984b-87c5c6640227/e26cda29-5355-40e2-8534-8247a2584df2.mp4",  
  "https://adint-assets.datamagic.rocks/3/34/341/3412/3412c/3412cd/3412cdaa-d346-400a-b58e-edd5f9ecca05/6af712fc-1806-4134-a0e4-d7a9505256d5.mp4",  
  "https://adint-assets.datamagic.rocks/f/f7/f71/f71f/f71f3/f71f36/f71f3621-7ffb-43d6-8e89-a9b464b529aa/48f8985a-9c3a-4130-b919-df4bb44f5878",  
  "https://adint-assets.datamagic.rocks/5/54/54d/54dd/54dd1/54dd11/54dd1192-dac7-47fc-b3da-51ad1bc472d2/7c8a20d8-6776-4e29-8b4f-4b66a3aac450",  
  "https://adint-assets.datamagic.rocks/1/17/174/174b/174b4/174b4c/174b4c91-6b00-41f3-8f80-074e4a893b12/e8ec12e2-1695-4958-8dcd-f87e62486b80.mp4",  
  "https://adint-assets.datamagic.rocks/5/5a/5aa/5aa6/5aa63/5aa63f/5aa63fe7-9805-453b-9e73-2a81629d691f/3e648404-8adf-446c-ba57-9a12cff81d55",  
  "https://adint-assets.datamagic.rocks/8/8f/8fc/8fc7/8fc7e/8fc7ec/8fc7ecfa-e696-4dfe-9a5c-6738c983b0f1/861aba24-4fb5-4758-9b37-a2679321f7de",  
  "https://adint-assets.datamagic.rocks/0/0d/0d9/0d96/0d96f/0d96ff/0d96ffe1-8c0f-4099-b990-13150b343e15/a8d27058-4738-4e3c-869e-5b68a2a1709b",  
  "https://adint-assets.datamagic.rocks/b/bf/bfe/bfe1/bfe14/bfe149/bfe149fd-df10-4c7b-95a6-4f5d43c9c368/617b1458-f187-4ab2-bf73-c5b1afacc97f",  
  "https://adint-assets.datamagic.rocks/7/7a/7a0/7a03/7a039/7a039a/7a039a43-1240-4fa3-8f51-346ae4db9c6a/87065cf5-3df9-412a-8e54-1b62958963d1",  
  "https://adint-assets.datamagic.rocks/b/b1/b1e/b1ed/b1eda/b1eda7/b1eda7b8-fea3-4094-a437-3c3fa3b8ae96/e4dc1045-ed6c-491c-877a-90ac3e9860d7",  
]

print(handle('https://adint-assets.datamagic.rocks/yt/R/R2/R2Z/R2Zr/R2ZrH/R2ZrHf/R2ZrHfHFWbw.mp4', "video"))
# for u in arr:
#     print(handle(u, "video"))
# #     # Example usage

  #3 min 8 sec
  # 50 sec
  # 1min
  # 2min 42 sec
  # 1min 30 sec
  # 1min
  # 1min 30 sec
  # 1min 48 sec
  # 1min 3 sec
  # 1min
  # 1min 45 sec
  # 1min 55 sec
  # 2min 39sec
  # 1min 40sec
  # 1min 10 sec
  # 1min 30sec
  # 1min 2 sec
  # 2min 21sec
  # 1 min 30 sec
  # 1min 49 sec