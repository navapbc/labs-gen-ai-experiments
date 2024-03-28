import dotenv
import requests
import os

dotenv.load_dotenv()


GURU_ENDPOINT = "https://api.getguru.com/api/v1/"
def get_guru_data():
    url = f"{GURU_ENDPOINT}cards/3fbff9c4-56a8-4561-a7d1-09727f1b4703"
    headers = {
    'Authorization': os.environ.get('GURU_TOKEN')}
    response = requests.request("GET", url, headers=headers)
    return response.json()