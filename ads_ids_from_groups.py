import requests
import json

def ads_id_from_api(group_id):
    result = []
    url = f"http://localhost:50325/api/v1/user/list?group_id={group_id}&page=1&page_size=100"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    data = json.loads(response.text)

    for item in data["data"]["list"]:
        result.append(item['user_id'])
    result.reverse()
    return result


def ads_groups_from_api():
    result = {}
    url = "http://localhost:50325/api/v1/group/list?page=1&page_size=15"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    data = json.loads(response.text)

    for item in data["data"]["list"]:
        result[item['group_id']] = item['group_name']

    return result