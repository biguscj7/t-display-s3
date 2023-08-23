import urequests
import network
import hashlib

INIT_URL = "https://app.thequietworkplace.com/api/external/init"
DISPLAY_URL = "https://app.thequietworkplace.com/api/external/room/display"

wlan = network.WLAN(network.STA_IF)


device_dict = {
    "device-id": wlan.config('mac').hex(),
    "pin": hashlib.sha1(wlan.config('mac').hex()).digest().hex()
}


def print_resp_info(resp):
    print(f"Status code: {resp.status_code}")
    print(f"Resp text: {resp.text}")


def register_device():
    init_headers = {**device_dict, **{"device-type": "unit_display"}}
    try:
        init_resp = urequests.get(INIT_URL, headers=init_headers)

        if init_resp.status_code == 200:
            return init_resp.status_code, init_resp.json()  # {"room_id":"5552f269-e0c3-4a39-8f40-4f7a3ead3887","display":"Q1","offset":240}
        else:
            return init_resp.status_code, init_resp.text
    except OSError as e:
        print(f"Check reservation call error: {e}")
        return 999, f"Error: {e}"


def check_reservation():
    try:
        res_resp = urequests.get(DISPLAY_URL, headers=device_dict)

        if res_resp.status_code == 200:
            return res_resp.status_code, res_resp.json()
        else:
            return res_resp.status_code, res_resp.text
    except OSError as e:
        print(f"Check reservation call error: {e}")
        return 999, f"Error: {e}"
