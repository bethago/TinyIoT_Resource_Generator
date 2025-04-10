import os
import sys
import json
import requests

SERVER_URL = 'http://127.0.0.1:3000'

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

getHeaders = {
    'Accept': 'application/json',
    'X-M2M-Origin': 'CAdmin',
    'X-M2M-RVI': '3',
    'X-M2M-RI': 'check_resource'
}

def request_post(url, headers, body):
    return requests.post(url, headers=headers, json=body).status_code == 201

def check_and_create_ae(url, parent_rn, ae_attrs):
    ae_rn = ae_attrs.get('rn')
    origin = f'C{ae_rn}' if ae_rn else 'CAdmin'
    headers = Headers(content_type='ae', origin=origin, ri='create_ae').headers
    if requests.get(f'{url}/{parent_rn}/{ae_rn}', headers=getHeaders).status_code == 200: return True, origin

    ae_body = {
        "m2m:ae": {
            "rn": ae_rn,
            "api": ae_attrs.get('api', f'N{parent_rn}'),
            "rr": ae_attrs.get('rr', True),
            "lbl": ae_attrs.get('lbl', []),
            "srv": ae_attrs.get('srv', ["3"])
        }
    }
    return request_post(f'{url}/{parent_rn}', headers, ae_body), origin

def check_and_create_cnt(url, parent_rn, cnt_attrs, origin):
    cnt_rn = cnt_attrs.get('rn')
    headers = Headers(content_type='cnt', origin=origin, ri='create_cnt').headers
    if requests.get(f'{url}/{parent_rn}/{cnt_rn}', headers=getHeaders).status_code == 200: return True
    cnt_body = {
        "m2m:cnt": {
            "rn": cnt_rn,
            "lbl": cnt_attrs.get('lbl', [])
        }
    }
    return request_post(f'{url}/{parent_rn}', headers, cnt_body)

def check_and_create_grp(url, parent_rn, grp_attrs):
    grp_rn = grp_attrs.get('rn')
    origin = f'C{grp_rn}' if grp_rn else 'CAdmin'
    mid = grp_attrs.get('mid')
    headers = Headers(content_type='grp', origin=origin, ri='create_grp').headers
    if requests.get(f'{url}/{parent_rn}/{grp_rn}', headers=getHeaders).status_code == 200: return True
    grp_body = {
        "m2m:grp": {
            "rn": grp_rn,
            "mid": mid,
            "mnm": len(mid),
            "mt": 3,
            "csy": 3
        }
    }
    return request_post(f'{url}/{parent_rn}', headers, grp_body)

def process_tasks(parent_rn, tasks, origin):
    stack = [(parent_rn, tasks, origin)]
    while stack:
        current_parent, current_tasks, current_origin = stack.pop()
        for task in current_tasks:
            if task.get('ty') == 2:
                ae_attrs = task['attrs']
                ae_rn = ae_attrs.get('rn')
                success, ae_origin = check_and_create_ae(SERVER_URL, current_parent, ae_attrs)
                if success:
                    print(f"AE '{ae_rn}' is ready under '{current_parent}'.")
                    if 'tasks' in task:
                        stack.append((f'{current_parent}/{ae_rn}', task['tasks'], ae_origin))
                else:
                    print(f"AE '{ae_rn}' is NOT ready under '{current_parent}'.")
            elif task.get('ty') == 3:
                cnt_attrs = task['attrs']
                cnt_rn = cnt_attrs.get('rn')
                if check_and_create_cnt(SERVER_URL, current_parent, cnt_attrs, current_origin):
                    print(f"CNT '{cnt_rn}' is ready under '{current_parent}'.")
                    if 'tasks' in task:
                        stack.append((f'{current_parent}/{cnt_rn}', task['tasks'], current_origin))
                else:
                    print(f"CNT '{cnt_rn}' is NOT ready under '{current_parent}'.")
            elif task.get('ty') == 9:
                grp_attrs = task['attrs']
                grp_rn = grp_attrs.get('rn')
                if check_and_create_grp(SERVER_URL, current_parent, grp_attrs):
                    print(f"GRP '{grp_rn}' is ready under '{current_parent}'.")
                else:
                    print(f"GRP '{grp_rn}' is NOT ready under '{current_parent}'.")

# main process
if len(sys.argv) > 1:
    input_file = sys.argv[1]
    if not input_file.endswith('.json'):
        print("Only JSON files are supported.")
        quit()
    if not os.path.exists(f'./data/{input_file}'):
        print(f"File {input_file} not found in ./data/")
        quit()
else:
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
        input_file = json_files[choice]
    except ValueError:
        print("Invalid input.")
        quit()

try:
    with open(f'./data/{input_file}', 'r', encoding='utf-8') as file:
        json_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    print("Failed to load the file.")
    quit()

cse_data = json_data[0]
if cse_data.get('ty') == 5 and 'tasks' in cse_data:
    process_tasks(cse_data['attrs']['rn'], cse_data['tasks'], 'CAdmin')
else:
    print("No valid Entity found in the selected JSON file.")
