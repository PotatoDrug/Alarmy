import sys
import time
import adafruit_matrixkeypad
from digitalio import DigitalInOut
import board
from models import Device
from config import config
from db import session
from utils import Thread


class KeyLock():
    def __init__(self, hwalert, lcd):
        self.code = ''
        self.hwalert = hwalert
        self.armed = False
        self.thread = None
        self.lcd = lcd
        # 4x4 matrix keypad
        rows = [DigitalInOut(x) for x in (board.D4, board.D17, board.D27, board.D22)]
        cols = [DigitalInOut(x) for x in (board.D18, board.D23, board.D24, board.D25)]
        keys = (('1', '2', '3', 'A'),
                ('4', '5', '6', 'B'),
                ('7', '8', '9', 'C'),
                ('*', '0', '#', 'D'))

        self.keypad = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keys)

    def enter_key(self, key):
        if not self.armed:
            device = session.query(Device).first()
            self.armed = device.alarm
        if self.armed:
            self.code = self.code + key
            length = len(self.code)
            self.lcd.text('*' * length, 2)

    def clear(self):
        self.code = ''
        self.lcd.text(self.hwalert.msg, 2)

    def disarm(self):
        self.hwalert.stop_alert()
        self.armed = False

    def authenticate(self):
        if config.KEYPAD_CODE == self.code:
            self.disarm()
            device = session.query(Device).first()
            device.alarm = False
            session.commit()
        else:
            self.lcd.text('Incorrect!', 2)
            time.sleep(1)
            self.clear()

    def check_keypad_input(self):
        while True:
            keys = self.keypad.pressed_keys
            if keys:
                if keys[0] == 'C':
                    self.clear()
                elif keys[0] == '*':
                    self.authenticate()
                else:
                    self.enter_key(keys[0])
                time.sleep(0.2)
    
    def start(self):
        self.thread = Thread(self.check_keypad_input)
