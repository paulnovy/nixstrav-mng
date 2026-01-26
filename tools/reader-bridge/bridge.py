import time
import threading
from ctypes import *

from flask import Flask, jsonify, request
from flask_cors import CORS
import serial.tools.list_ports

DLL_NAME = "UHFPrimeReader.dll"
DEFAULT_BAUD = 115200


class Api:
    def __init__(self):
        self.lib = cdll.LoadLibrary(DLL_NAME)
        self.lib.OpenDevice.restype = c_int32
        self.lib.CloseDevice.restype = c_int32
        self.lib.GetDevicePara.restype = c_int32
        self.lib.SetDevicePara.restype = c_int32
        self.lib.GetTagUii.restype = c_int32
        self.lib.InventoryContinue.restype = c_int32
        self.lib.InventoryStop.restype = c_int32

    def OpenDevice(self, hComm, port, baudrate):
        return self.lib.OpenDevice(byref(hComm), port, baudrate)

    def CloseDevice(self, hComm):
        return self.lib.CloseDevice(hComm)

    def GetDevicePara(self, hComm, param):
        return self.lib.GetDevicePara(hComm, byref(param))

    def SetDevicePara(self, hComm, param):
        return self.lib.SetDevicePara(hComm, param)

    def GetTagUii(self, hComm, tagInfo, timeout):
        return self.lib.GetTagUii(hComm, byref(tagInfo), timeout)

    def InventoryContinue(self, hComm, invCount, invParam):
        return self.lib.InventoryContinue(hComm, invCount, invParam)

    def InventoryStop(self, hComm, timeout):
        return self.lib.InventoryStop(hComm, timeout)


class DeviceFullInfo(Structure):
    _fields_ = [
        ("DEVICEARRD", c_ubyte),
        ("RFIDPRO", c_ubyte),
        ("WORKMODE", c_ubyte),
        ("INTERFACE", c_ubyte),
        ("BAUDRATE", c_ubyte),
        ("WGSET", c_ubyte),
        ("ANT", c_ubyte),
        ("REGION", c_ubyte),
        ("STRATFREI", c_ubyte * 2),
        ("STRATFRED", c_ubyte * 2),
        ("STEPFRE", c_ubyte * 2),
        ("CN", c_ubyte),
        ("RFIDPOWER", c_ubyte),
        ("INVENTORYAREA", c_ubyte),
        ("QVALUE", c_ubyte),
        ("SESSION", c_ubyte),
        ("ACSADDR", c_ubyte),
        ("ACSDATALEN", c_ubyte),
        ("FILTERTIME", c_ubyte),
        ("TRIGGLETIME", c_ubyte),
        ("BUZZERTIME", c_ubyte),
        ("INTERNELTIME", c_ubyte),
    ]


class DevicePara(Structure):
    _fields_ = DeviceFullInfo._fields_


class TagInfo(Structure):
    _fields_ = [
        ("m_no", c_ushort),
        ("m_rssi", c_short),
        ("m_ant", c_ubyte),
        ("m_channel", c_ubyte),
        ("m_crc", c_ubyte * 2),
        ("m_pc", c_ubyte * 2),
        ("m_len", c_ubyte),
        ("m_code", c_ubyte * 255),
    ]


def hex_array_to_string(array, length):
    if length <= 0:
        return ""
    return " ".join(hex(array[i]).replace("0x", "").zfill(2) for i in range(length))


class InventoryThread(threading.Thread):
    def __init__(self, api, hcomm):
        super().__init__(daemon=True)
        self.api = api
        self.hcomm = hcomm
        self.info = {}
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        while not self._stop.is_set():
            tag = TagInfo()
            res = self.api.GetTagUii(self.hcomm, tag, 1000)
            if res != 0:
                continue
            length = tag.m_len
            if length <= 0:
                continue
            epc = hex_array_to_string(list(tag.m_code), length)
            self.info[epc] = {
                "epc": epc,
                "rssi": tag.m_rssi / 10,
                "ant": tag.m_ant,
                "channel": tag.m_channel,
                "counts": self.info.get(epc, {}).get("counts", 0) + 1,
                "ts": time.time(),
            }


app = Flask(__name__)
CORS(app)
api = Api()

state = {
    "hcomm": 0,
    "thread": None,
}


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/ports")
def ports():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return jsonify({"ok": True, "ports": ports})


def baud_to_code(baudrate: int) -> int:
    mapping = {9600: 0, 19200: 1, 38400: 2, 57600: 3, 115200: 4}
    return mapping.get(baudrate, 4)


@app.post("/open")
def open_device():
    data = request.get_json(force=True, silent=True) or {}
    port = data.get("port")
    baudrate = int(data.get("baudrate") or DEFAULT_BAUD)
    if not port:
        return jsonify({"ok": False, "error": "port required"}), 400
    hcomm = c_int()
    res = api.OpenDevice(hcomm, c_char_p(port.encode("utf-8")), c_ubyte(baud_to_code(baudrate)))
    if res != 0:
        return jsonify({"ok": False, "error": f"OpenDevice failed: {res}"}), 500
    state["hcomm"] = hcomm.value
    return jsonify({"ok": True, "handle": hcomm.value})


@app.post("/start")
def start_inventory():
    if not state["hcomm"]:
        return jsonify({"ok": False, "error": "reader not open"}), 400
    hcomm = c_int(state["hcomm"])
    param = DeviceFullInfo()
    api.GetDevicePara(hcomm, param)
    api.SetDevicePara(hcomm, DevicePara(*[getattr(param, field[0]) for field in DevicePara._fields_]))
    api.InventoryContinue(hcomm, c_ubyte(0), c_int(0))
    if state["thread"]:
        state["thread"].stop()
    t = InventoryThread(api, hcomm)
    state["thread"] = t
    t.start()
    return jsonify({"ok": True})


@app.post("/tags")
def tags():
    t = state.get("thread")
    if not t:
        return jsonify({"ok": True, "tags": []})
    tags_sorted = sorted(t.info.values(), key=lambda x: x["ts"], reverse=True)
    return jsonify({"ok": True, "tags": tags_sorted})


@app.post("/stop")
def stop_inventory():
    if not state["hcomm"]:
        return jsonify({"ok": True})
    hcomm = c_int(state["hcomm"])
    if state["thread"]:
        state["thread"].stop()
        state["thread"] = None
    api.InventoryStop(hcomm, 1000)
    return jsonify({"ok": True})


@app.post("/close")
def close_device():
    if not state["hcomm"]:
        return jsonify({"ok": True})
    hcomm = c_int(state["hcomm"])
    api.CloseDevice(hcomm)
    state["hcomm"] = 0
    if state["thread"]:
        state["thread"].stop()
        state["thread"] = None
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)
