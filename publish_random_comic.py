import os
import random

from dotenv import load_dotenv
import requests


def main():
    load_dotenv()
    publish_new_comic_post()


def publish_new_comic_post():
    image_name, image_info = download_random_comic()
    try:
        message = build_comic_message(image_info)
        post_comic_on_wall(image_name, message)
    finally:
        os.remove(image_name)


def download_random_comic():
    random_comic_number = get_random_comic_number()
    url = f'https://xkcd.com/{random_comic_number}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    img_info = response.json()
    img_url = img_info['img']
    img_name = os.path.split(img_url)[-1]
    download_image(img_url, img_name)
    return img_name, img_info


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


def build_comic_message(image_info):
    title = image_info['title']
    comment = image_info['alt']
    message = f'{title}.\n{comment}'
    return message


def post_comic_on_wall(image_name, message):
    vk_group_id = os.getenv('VK_GROUP_ID')
    photo_attribs = save_to_album(image_name, vk_group_id)
    photo_owner_id = photo_attribs['owner_id']
    photo_id = photo_attribs['id']
    attachment = f'photo{photo_owner_id}_{photo_id}'
    publish_post_on_wall(message, attachment, vk_group_id)


def save_to_album(image_name, vk_group_id):
    save_params = vk_upload_on_serv(image_name, vk_group_id)
    method_name = 'photos.saveWallPhoto'
    payload = {
        'group_id': vk_group_id,
        'server': save_params['server'],
        'photo': save_params['photo'],
        'hash': save_params['hash'],
    }
    response = make_vk_api_request(method_name, payload)
    photo_attributes = response['response'][0]
    return photo_attributes


def vk_upload_on_serv(image_name, vk_group_id):
    upload_url = vk_get_upload_url(vk_group_id)
    with open(f'{image_name}', 'rb') as photo:
        file = {'photo': photo}
        response = requests.post(upload_url, files=file)
    response.raise_for_status()
    save_params = response.json()
    return save_params


def vk_get_upload_url(vk_group_id):
    method_name = 'photos.getWallUploadServer'
    payload = {'group_id': vk_group_id}
    api_response = make_vk_api_request(method_name, payload)
    upload_url = api_response['response']['upload_url']
    return upload_url


def make_vk_api_request(method_name, payload):
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_api_version = '5.101'
    vk_url = f'https://api.vk.com/method/{method_name}'
    vk_required_params = {
        'access_token': f'{vk_access_token}',
        'v': f'{vk_api_version}'
    }
    payload.update(vk_required_params)
    response = requests.post(vk_url, params=payload).json()
    try:
        error_msg = response['error']['error_msg']
        raise Exception(f'vk api request error. {error_msg}')
    except KeyError:
        return response


def publish_post_on_wall(message, attachments, vk_group_id):
    method_name = 'wall.post'
    payload = {
        'owner_id': f'-{vk_group_id}',
        'from_group': '1',
        'message': message,
        'attachments': attachments,
    }
    make_vk_api_request(method_name, payload)


if __name__ == '__main__':
    main()
