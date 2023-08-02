import requests
from datetime import datetime as dt
import time
from tqdm import tqdm
from pprint import pprint
from pydrive.auth import GoogleAuth
import io
import json
import configparser

class VK:

    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def users_albums_info(self):
        url = 'https://api.vk.com/method/photos.getAlbums'
        params = {'owner_id': self.id, 'need_system': '1'}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    @staticmethod
    def select_album_for_upload(users_albums_info):
        print(f'Доступные альбомы фотографий:\n'
              f'|')
        for albums_ind in range(len(users_albums_info['response']['items'])):
            print(f"|- {albums_ind + 1}. [{users_albums_info['response']['items'][albums_ind]['title']}], "
                  f"({users_albums_info['response']['items'][albums_ind]['size']} фото)")
        print()
        selected_album = input('Введите номер альбома для сохранения на облачный сервис: ')
        if not selected_album.isdigit() \
                or int(selected_album) not in range(1, len(users_albums_info['response']['items']) + 1):
            print('Ошибка! Введен некорректный номер альбома!')
            return False
        num_of_photos = input('Введите количество фотографий выбранного альбома для сохранения на облачный сервис: ')
        if not num_of_photos.isdigit() \
                or int(num_of_photos) not in range(1, users_albums_info['response']['items'][int(selected_album) - 1][
                                                          'size'] + 1):
            print('Ошибка! Введено некорректное количество фотографий!')
            return False
        print(f"Выбран альбом [{users_albums_info['response']['items'][int(selected_album) - 1]['title']}], "
              f"количество фотографий "
              f"[{int(num_of_photos)}/{users_albums_info['response']['items'][int(selected_album) - 1]['size']}]")
        return {'album_id': users_albums_info['response']['items'][int(selected_album) - 1]['id'],
                'number_of_photos': num_of_photos,
                'album_title': users_albums_info['response']['items'][int(selected_album) - 1]['title']}

    def users_photos_info(self, album_id, number_of_photos):
        photos_info = []
        file_names = []
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, 'album_id': album_id, 'extended': '1',
                  'photo_sizes': '1', 'count': number_of_photos}
        response = requests.get(url, params={**self.params, **params})
        for ph_ind in range(len(response.json()['response']['items'])):
            file_names.append(str(response.json()['response']['items'][ph_ind]['likes']['count']))
            photos_info.append(
                {'file_name': str(response.json()['response']['items'][ph_ind]['likes']['count']),
                 'size': response.json()['response']['items'][ph_ind]['sizes'][-1]['type'],
                 'vk_photo_url': response.json()['response']['items'][ph_ind]['sizes'][-1]['url'],
                 'date': dt.fromtimestamp(response.json()['response']['items'][ph_ind]['date']).strftime(
                     '%d.%m.%Y_%Hч_%Mм_%Sс')})
        duplicate_file_names = [file_names[i] for i in range(len(file_names)) if i != file_names.index(file_names[i])]
        for ph_ind in range(len(photos_info)):
            if photos_info[ph_ind]['file_name'] in duplicate_file_names:
                photos_info[ph_ind]['file_name'] += '_' + photos_info[ph_ind]['date'] + '.jpg'
            else:
                photos_info[ph_ind]['file_name'] += '.jpg'
        return photos_info


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def check_folder(self, folder_name):
        folders = []
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': '/'}
        headers = {'Authorization': f'OAuth {self.token}', 'Accept': 'application/json'}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            for item in range(len(response.json()['_embedded']['items'])):
                if response.json()['_embedded']['items'][item]['type'] == 'dir':
                    folders.append(response.json()['_embedded']['items'][item]['name'])
            if folder_name not in folders:
                return False
            else:
                return True

    def upload_photo(self, file_path, photo_url):
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {'path': file_path, 'url': photo_url, }
        headers = {'Authorization': f'OAuth {self.token}'}
        response = requests.post(url, params=params, headers=headers)
        response_status_operation = requests.get(response.json()['href'], headers=headers)
        while response_status_operation.json()['status'] != 'success':
            if response_status_operation.json()['status'] == 'failed':
                print('Ошибка! Скопировать файл не удалось, переходим к следующему')
                return
            else:
                time.sleep(1)
                response_status_operation = requests.get(response.json()['href'], headers=headers)
        return response.status_code

    def create_folder(self, folder_name):
        create_folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {'Authorization': f'OAuth {self.token}'}
        params = {'path': folder_name}
        response = requests.put(create_folder_url, params=params, headers=headers)
        if response.status_code == 201:
            print('Папка успешно создана')
        else:
            print(f"Ошибка! {response.json()['message']}")
        return response.status_code

    def files_on_disk(self):
        url = 'https://cloud-api.yandex.net/v1/disk/resources/files'
        headers = {'Authorization': f'OAuth {self.token}'}
        pprint(f'Информация о файлах на диске:{requests.get(url, headers=headers).json()}')
        return


class GDrive:
    def __init__(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        token = gauth.attr['credentials'].access_token
        self.access_token = token

    def check_folder(self, folder_name):
        url = 'https://www.googleapis.com/drive/v3/files'
        headers = {'Authorization': 'Bearer ' + self.access_token}
        params = {'q': "name = '" + folder_name + "'"}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            for item in range(len(response.json()['files'])):
                if response.json()['files'][item]['mimeType'] == 'application/vnd.google-apps.folder':
                    return response.json()['files'][0]['id']
        return False

    def create_folder(self, folder_name):
        url = 'https://www.googleapis.com/upload/drive/v3/files'
        headers = {'Authorization': 'Bearer ' + self.access_token}
        metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
        files = {'data': ('metadata', json.dumps(metadata), 'application/json')}
        response = requests.post(url, files=files, headers=headers)
        if response.status_code == 200:
            print('Папка успешно создана')
            return response.json()['id']
        else:
            print(f"Ошибка! {response.json()['error']['message']}")
        return 'error'

    def upload_photo(self, folder_id, filename, photo_url):
        url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true'
        metadata = {"name": filename, "parents": [folder_id]}
        files = {'data': ('metadata', json.dumps(metadata), 'application/json'),
                 'file': io.BytesIO(requests.get(photo_url).content)}
        response = requests.post(url, files=files, headers={"Authorization": "Bearer " + self.access_token})
        return response.status_code


def write_json_file(photos_for_upload):
    for i in range(len(photos_for_upload)):
        del photos_for_upload[i]['date']
        del photos_for_upload[i]['vk_photo_url']
    with open('photos.json', 'w', encoding='utf-8') as file:
        json.dump(photos_for_upload, file, ensure_ascii=False, indent=2)
        print('Файл photos.json cоздан')
    return


def main():
    config = configparser.ConfigParser()
    config.read('settings.ini')

    access_token_vk = config['VK']['token']
    access_token_ya = config['YADisk']['token']

    user_id = input('Введите id аккаунта VK: ')
    vk = VK(access_token_vk, user_id)
    ya_disk = YaUploader(access_token_ya)

    user_name = vk.users_info()
    if len(user_name['response']) == 0:
        print('Введен некорректный id')
        return
    else:
        print(f"Имя: {user_name['response'][0]['first_name']} {user_name['response'][0]['last_name']}")

    albums = vk.users_albums_info()
    selected_album_for_upload = vk.select_album_for_upload(albums)
    if not selected_album_for_upload:
        return
    else:
        selected_photos_for_upload = vk.users_photos_info(selected_album_for_upload['album_id'],
                                                          selected_album_for_upload['number_of_photos'])

    folder_for_upload = input('Введите название папки для загрузки или оставьте поле пустым и нажмите [Enter], '
                              'чтобы именем папки являлось имя альбома: ')
    if folder_for_upload == '':
        folder_for_upload = selected_album_for_upload['album_title']
    # Выбираем целевой диск
    select_cloud_service = input('Выберите облачный сервис для загрузки: [1] - Яндекс.Диск, [2] - GoogleDrive: ')
    if select_cloud_service not in ('1', '2'):
        return print('Введено неверное значение. Необходимо ввести 1 или 2')
    # Работаем с Я.Диск
    elif select_cloud_service == '1':
        print('Проверяем есть ли указанная папка в корневой директории яндекс.диска...')
        if not ya_disk.check_folder(folder_for_upload):
            print('Папка отсутствует. Создаём...')
            if ya_disk.create_folder(folder_for_upload) != 201:
                return
            else:
                print('Начинаем процесс копирования...')
        else:
            print('Папка уже существует в директории. Начинаем процесс копироания...')

        for photo in tqdm(range(len(selected_photos_for_upload)), ncols=100, colour='white', desc='Прогресс загрузки',
                          bar_format='{desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt}'):
            if ya_disk.upload_photo(folder_for_upload + '/' + selected_photos_for_upload[photo]['file_name'],
                                    selected_photos_for_upload[photo]['vk_photo_url']) != 202:
                print('Ошибка выполнения операции')
    # Работаем с Google Disk
    elif select_cloud_service == '2':
        gdisk = GDrive()
        print('Проверяем есть ли указанная папка в корневой директории яндекс.диска...')
        gdisk_folder_id = gdisk.check_folder(folder_for_upload)
        if not gdisk_folder_id:
            print('Папка отсутствует. Создаём...')
            gdisk_folder_id = gdisk.create_folder(folder_for_upload)
            if gdisk_folder_id == 'error':
                return
            else:
                print('Начинаем процесс копирования...')
        else:
            print('Папка уже существует в директории. Начинаем процесс копироания...')

        for photo in tqdm(range(len(selected_photos_for_upload)), ncols=100, colour='white', desc='Прогресс загрузки',
                          bar_format='{desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt}'):
            if gdisk.upload_photo(gdisk_folder_id, selected_photos_for_upload[photo]['file_name'],
                                  selected_photos_for_upload[photo]['vk_photo_url']) != 200:
                print('Ошибка загрузки файла')

    print('Копирование фотографий завершено! Создаем файл json с информацией о файлах')

    write_json_file(selected_photos_for_upload)

    print('Выполнение программы завершено')


if __name__ == '__main__':
    main()
