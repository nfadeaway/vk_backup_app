# О проекте
![Static Badge](https://img.shields.io/badge/python%20-%20black?logo=python&logoColor=%23FFDE56)

[Курсовая работа "Резервное копирование"](https://github.com/netology-code/py-diplom-basic)

Программа для копирования фотографий из альбомов пользователей социальной сети "ВКонтакте" в облачные хранилища: Я.Диск, Google Диск.

## Дополнительная информация
Для работы программы необходимо получить:
- [персональный токен VK](https://dev.vk.com/api/access-token/getting-started)
- [токен Я.Диск](https://yandex.ru/dev/disk/poligon/)
- [файл `client_secrets.json`](https://support.google.com/cloud/answer/6158849?hl=en)

Для доступа к собственным альбомам в правах токена VK в scope должен быть прописан атрибут `photos`.
Для доступа к чужим открытым альбомам этот параметр не требуется.

## Настройки программы
Токены, необходимые для работы, должны быть внесены в файл `settings.ini`, находящийся в папке с программой, в формате:
```
[VK]
token=

[YADisk]
token=
```
Для работы с GoogleDrive используется библиотека **pydrive**. Файл `client_secrets.json` должен находиться в папке с программой.

## Запись работы программы
![Работа программы](/gif/vk_backup_app.gif)
