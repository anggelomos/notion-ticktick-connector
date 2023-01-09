import json
import http.client


class TicktickAPI:
    
    BASE_URL = "/api/v2"
    signin_url = BASE_URL+"/user/signin?wc=True&remember=True"

    def __init__(self, username: str, password: str):
        self.token = self.login(username, password)

    def login(self, user: str, password: str) -> str:
        payload = {
            "username": user,
            "password": password
        }

        response = self.post(self.signin_url, payload)
        return response["token"]

    def post(self, url: str, data=None, headers=None, token_required: bool = False) -> dict:
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        headers["Content-Type"] = "application/json"
        if token_required:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["Cookie"] = f"t={self.token}"

        conn = http.client.HTTPSConnection("api.ticktick.com")
        conn.request("POST", url, json.dumps(data), headers)
        res = conn.getresponse()
        response = json.loads(res.read().decode("utf-8"))
        return response

    def get(self, url: str, data=None, headers=None, token_required: bool = False) -> dict:
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        headers["Content-Type"] = "application/json"
        if token_required:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["Cookie"] = f"t={self.token}"

        conn = http.client.HTTPSConnection("api.ticktick.com")
        conn.request("GET", url, json.dumps(data), headers)
        res = conn.getresponse()
        response = json.loads(res.read().decode("utf-8"))
        return response
