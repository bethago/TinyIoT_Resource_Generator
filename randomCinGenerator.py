from random import randint
import requests

SERVER_URL = 'http://127.0.0.1:3000'

CNT_URI = {
    "TinyIoT/house/growth",
    "TinyIoT/house/moisture",
    "TinyIoT/house/sunshine",
    "TinyIoT/house/airquality",
    "TinyIoT/house/humidity",
    "TinyIoT/house/temperature"
}

headers = {
    'Accept': 'application/json',
    'X-M2M-Origin': 'CAdmin',
    'X-M2M-RVI': '3',
    'X-M2M-RI': 'randomCinTest',
    'Content-Type': f'application/json;ty=4'
}

def randomCin():
    for CNT in CNT_URI:
        body = {
            "m2m:cin": {
                "con": f'{randint(100, 999)}'
            }
        }
        status = requests.post(f'{SERVER_URL}/{CNT}', headers=headers, json=body)
        if status.status_code == 201:
            print( f"created cin under {CNT}")

randomCin()