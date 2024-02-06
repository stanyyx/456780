import datetime
import time
import requests


start = datetime.datetime.now()
print('запускаем метод post')
response = requests.post('http://127.0.0.1:5000/upscaling/', files={
    'file': open('lama_300px.png', 'rb')
}).json()
file_name = response['file_name']
task_id = response['task_id']
print(file_name, task_id)
print('\nзапускаем метод get')
status = 'PENDING'
while status == 'PENDING':
    response = requests.get(f'http://127.0.0.1:5000/upscaling/{task_id}/')
    response = response.json()
    print(response)
    status = response['status']
    if status == 'PENDING':
        time.sleep(1)
print(response)
print('\nЗапускаем второй метод get')
response = requests.get(f'http://127.0.0.1:5000/upscaled/{file_name}/')
print('Готово! В папку files загруженно обработанное изображение')
print(f'Затратило времени: {datetime.datetime.now() - start}')
