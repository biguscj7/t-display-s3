import urequests
import network
import hashlib

INIT_URL = "https://app.thequietworkplace.com/api/external/init"
DISPLAY_URL = "https://app.thequietworkplace.com/api/external/room/display"

wlan = network.WLAN(network.STA_IF)


def build_init_headers():
    device_id = wlan.config('mac').hex()
    pin = hashlib.sha1(device_id).digest().hex()
    device_type = "unit_display"
    return {"device-id": device_id, "pin": pin, "device-type": device_type}


def print_resp_info(resp):
    print(f"Status code: {resp.status_code}")
    print(f"Resp text: {resp.text}")


def build_reservation_headers():
    device_id = wlan.config('mac').hex()
    pin = hashlib.sha1(device_id).digest().hex()
    return {"device-id": device_id, "pin": pin}


def register_device():
    init_headers = build_init_headers()
    init_resp = urequests.get(INIT_URL, headers=init_headers)
    if init_resp.status_code == 200:
        return init_resp.status_code, init_resp.json()  # {"room_id":"5552f269-e0c3-4a39-8f40-4f7a3ead3887","display":"Q1","offset":240}
    else:
        return init_resp.status_code, init_resp.text


def check_reservation():
    res_headers = build_reservation_headers()
    res_resp = urequests.get(DISPLAY_URL, headers=res_headers)
    if res_resp.status_code == 200:
        return res_resp.status_code, res_resp.json()
    else:
        return res_resp.status_code, res_resp.text