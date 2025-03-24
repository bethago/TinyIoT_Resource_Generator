import os
import json
import requests

SERVER_URL = 'http://127.0.0.1:3000/TinyIoT'

class Headers:
    def __init__(self, content_type=None, origin='CAdmin', ri='request'):
        self.headers = {
            'Accept': 'application/json',
            'X-M2M-Origin': origin,
            'X-M2M-RVI': '3',
            'X-M2M-RI': ri,
            'Content-Type': f'application/json;ty={self.get_content_type(content_type)}' if content_type else 'application/json'
        }

    @staticmethod
    def get_content_type(content_type):
        return {'acp': 1, 'ae': 2, 'cnt': 3, 'cin': 4, 'cb': 5, 'grp': 9, 'sub': 23}.get(content_type)

def request_post(url, headers, body):
    return requests.post(url, headers=headers, json=body).status_code == 201

def check_and_create_ae(url, ae_attrs):
    ae_rn = ae_attrs.get('rn')
    origin = f'C{ae_rn[:5]}' if ae_rn else 'CAdmin'
    headers = Headers(content_type='ae', origin=origin, ri='create_ae').headers
    if requests.get(f'{url}/{ae_rn}', headers=headers).status_code == 200: return True, origin

    ae_body = {
        "m2m:ae": {
            "rn": ae_rn,
            "api": ae_attrs.get('api', f'N{ae_rn}'),
            "rr": ae_attrs.get('rr', True),
            "lbl": ae_attrs.get('lbl', []),
            "srv": ae_attrs.get('srv', ["3"])
        }
    }
    return request_post(url, headers, ae_body), origin

def check_and_create_cnt(url, ae_rn, cnt_attrs, origin):
    cnt_rn = cnt_attrs.get('rn')
    headers = Headers(content_type='cnt', origin=origin, ri='create_cnt').headers
    if requests.get(f'{url}/{ae_rn}/{cnt_rn}', headers=headers).status_code == 200: return True

    cnt_body = {
        "m2m:cnt": {
            "rn": cnt_rn,
            "lbl": cnt_attrs.get('lbl', []),
            "mbs": cnt_attrs.get('mbs', 16384)
        }
    }
    return request_post(f'{url}/{ae_rn}', headers, cnt_body)

def process_ae_and_cnt(tasks, url):
    for task in tasks:
        if task.get('ty') == 2:
            ae_attrs = task['attrs']
            ae_rn = ae_attrs.get('rn')
            success, origin = check_and_create_ae(url, ae_attrs)
            if success:
                print(f"AE '{ae_rn}' is ready.")
                for cnt_task in task.get('tasks', []):
                    if cnt_task.get('ty') == 3:
                        cnt_attrs = cnt_task['attrs']
                        cnt_rn = cnt_attrs.get('rn')
                        if check_and_create_cnt(url, ae_rn, cnt_attrs, origin):
                            print(f"CNT '{cnt_rn}' is ready under AE '{ae_rn}'.")

# main process
json_files = [f for f in os.listdir('./data/') if f.endswith('.json')]
if not json_files:
    print("No JSON files found in the /data/ folder.")
    quit()

for idx, file_name in enumerate(json_files):
    print(f"[{idx}] {file_name}")

try:
    choice = int(input("Enter the number of the file you want to read: "))
    if choice not in range(len(json_files)):
        print("Invalid number.")
        quit()
except ValueError:
    print("Invalid input.")
    quit()

try:
    with open(f'./data/{json_files[choice]}', 'r', encoding='utf-8') as file:
        json_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    print("Failed to load the file.")
    quit()

# TBD
cse_data = json_data[0]
if cse_data.get('ty') == 5 and 'tasks' in cse_data:
    process_ae_and_cnt(cse_data['tasks'], SERVER_URL)
else:
    print("No valid AE found in the selected JSON file.")
