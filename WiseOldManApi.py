import requests
from datetime import datetime

url = 'https://api.wiseoldman.net'

def createSOTW(title: str, metric: str, startsAt: datetime, endsAt: datetime, participants: list):
    endpoint = '/competitions'
    dateFormat = '%Y-%m-%dT%H:%M:%S.%fZ'
    params = {
        'title': title,
        'metric': metric,
        'startsAt': startsAt.strftime(dateFormat),
        'endsAt': endsAt.strftime(dateFormat),
        'participants': participants
    }
    requestUrl = url + endpoint
    return requests.post(requestUrl, data=params)
