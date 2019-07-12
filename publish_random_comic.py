import os
import requests
from dotenv import load_dotenv
import random


def main():
    load_dotenv()
    publish_new_comic_post()

def publish_new_comic_post():
    image_name, message = download_random_comic()
    post_comic_on_wall(image_name, message)
    os.remove(image_name)
    
def download_random_comic():
    random_comic_number = get_random_comic_number()
    url = f'https://xkcd.com/{random_comic_number}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    response = response.json()
    img_url = response['img']
    img_name = os.path.split(img_url)[-1]   
    title = response['title']
    comment = response['alt']
    message = f'{title}.\n{comment}'
    download_image(img_url, img_name)
    return img_name, message

def get_random_comic_number():
    number_of_comics = get_current_number_of_comics()
    random_comic_number = random.randint(1, number_of_comics)
    return random_comic_number

def get_current_number_of_comics():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    current_number = response.json()['num']
    return current_number

def download_image(url, image_name):
    response = requests.get(url)
    response.raise_for_status()
    with open(f'{image_name}', 'wb') as new_file:
        new_file.write(response.content)

def post_comic_on_wall(image_name, message):
    VK_GROUP_ID = os.getenv('VK_GROUP_ID')
    photo_attribs = save_to_album(image_name, VK_GROUP_ID)
    photo_owner_id = photo_attribs['owner_id']
    photo_id = photo_attribs['id']
    attachment = f'photo{photo_owner_id}_{photo_id}'
    publish_post_on_wall(message, attachment, VK_GROUP_ID)

def save_to_album(image_name, VK_GROUP_ID):
    save_params = vk_upload_on_serv(image_name, VK_GROUP_ID)
    payload = {
        'group_id': VK_GROUP_ID,
        'server': save_params['server'],
        'photo': save_params['photo'],
        'hash': save_params['hash'],
    }
    response = vk_api_request('photos.saveWallPhoto', payload)
    photo_attributes = response['response'][0]
    return photo_attributes

def vk_upload_on_serv(image_name, VK_GROUP_ID):
    upload_url = vk_get_upload_url(VK_GROUP_ID)
    with open(f'{image_name}', 'rb') as photo:
        file = {'photo': photo}
        response = requests.post(upload_url, files=file)
    response.raise_for_status()
    save_params = response.json()
    return save_params

def vk_get_upload_url(VK_GROUP_ID):
    method_name = 'photos.getWallUploadServer'
    payload = {'group_id': VK_GROUP_ID}
    api_response = vk_api_request(method_name, payload)
    upload_url = api_response['response']['upload_url']
    return upload_url

def vk_api_request(method_name, payload):
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_api_version = '5.101'
    vk_url = f'https://api.vk.com/method/{method_name}'
    vk_required_params = {
        'access_token': f'{vk_access_token}',
        'v': f'{vk_api_version}'
    }
    payload.update(vk_required_params) 
    response = requests.post(vk_url, params=payload)
    response.raise_for_status()
    return response.json()

def publish_post_on_wall(message, attachments, VK_GROUP_ID):
    VK_GROUP_ID = f'-{VK_GROUP_ID}'
    payload = {
        'owner_id': VK_GROUP_ID,
        'from_group': '1',
        'message': message,
        'attachments': attachments,        
    }
    vk_api_request('wall.post', payload)

if __name__ == '__main__':
    main()