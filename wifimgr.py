import network
import ure
import time

NETWORK_PROFILES = 'data.txt'
HOSTNAME = "Q6-timer-display"

wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
time.sleep(3)
wlan_sta.config(reconnects=2, dhcp_hostname=HOSTNAME)

server_socket = None


def get_connection():
    """return a working WLAN(STA_IF) instance or None"""

    # First check if there already is any connection:
    if wlan_sta.isconnected():
        return wlan_sta

    connected = False
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if wlan_sta.isconnected():
            return wlan_sta

        # Read known network profiles from file
        profiles = read_profiles()

        # Search WiFis in range
        wlan_sta.active(True)
        networks = wlan_sta.scan()

        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            encrypted = authmode > 0
            print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = do_connect(ssid, password, bssid)
                else:
                    print("skipping unknown encrypted network")
            if connected:
                break

    except OSError as e:
        print("exception", e)

    return wlan_sta if connected else None


def read_profiles():
    with open(NETWORK_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")
        profiles[ssid] = password
    return profiles


def do_connect(ssid, password, bssid):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        return None

    wlan_sta.disconnect()

    print('Trying to connect to %s...' % ssid)
    print("Using pw: %s" % password)
    wlan_sta.connect(ssid, password, bssid=bssid)
    while wlan_sta.status() == network.STAT_CONNECTING:
        time.sleep(0.1)
        print('.', end='')

    if wlan_sta.isconnected():
        print('\nConnected. Network config: ', wlan_sta.ifconfig())
    else:
        print('\nFailed. Not Connected to: ' + ssid)
    return wlan_sta.isconnected()
