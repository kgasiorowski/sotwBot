import requests
from datetime import datetime
import json

url = 'https://api.wiseoldman.net'

def createSOTW(
        title: str,
        metric: str,
        startsAt: datetime,
        endsAt: datetime,
        participants: list=None,
        groupId: int=None,
        groupVerificationCode: str=None
        ):
    endpoint = '/competitions'
    dateFormat = '%Y-%m-%dT%H:%M:%S.%fZ'
    params = {
        'title': title,
        'metric': metric,
        'startsAt': startsAt.strftime(dateFormat),
        'endsAt': endsAt.strftime(dateFormat)
    }
    if participants is not None:
        params.setdefault('participants', participants)
    else:
        params.setdefault('groupId', groupId)
        params.setdefault('groupVerificationCode', groupVerificationCode)
    requestUrl = url + endpoint
    response = requests.post(requestUrl, data=params)

    if response.status_code >= 300:
        return False
    else:
        return json.loads(response.content.decode())

def deleteSotw(sotwId: int, verificationCode: str):
    endpoint = f'/competitions/{sotwId}'
    requestUrl = url + endpoint
    params = {'verificationCode':verificationCode}
    response = requests.delete(requestUrl, data=params)
    if response.status_code >= 300:
        return False
    else:
        return json.loads(response.content.decode())

def getSotw(sotwId: int):
    endpoint = f'/competitions/{sotwId}'
    requestUrl = url + endpoint
    response = requests.get(requestUrl)
    if response.status_code >= 300:
        return False
    else:
        return json.loads(response.content.decode())