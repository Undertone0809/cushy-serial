# Copyright (c) 2023 Zeeland
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright Owner: Zeeland
# GitHub Link: https://github.com/Undertone0809/
# Project Link: https://github.com/Undertone0809/cushy-serial
# Contact Email: zeeland@foxmail.com

import serial
import logging

from serial.serialutil import *
from typing import Callable, List, Optional
from concurrent.futures import ThreadPoolExecutor

__all__ = ['CushySerial', 'enable_log']
logger = logging.getLogger(__name__)


def enable_log():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class CushySerial(serial.Serial):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self._executor = ThreadPoolExecutor()
        self._callbacks: List[Callable] = []
        self._cur_msg: Optional[bytes] = None
        self._is_listening: bool = False

    def send(self, msg: str or bytes):
        """
        send message to serial. You can input str or bytes data type as the message.
        """
        if not self.is_open:
            raise PortNotOpenError()
        if type(msg) == str:
            self.write(msg.encode())
        elif type(msg) == bytes:
            self.write(msg)
        self.flush()

    def polling_task(self, msg: str or bytes, interval: float, times: Optional[int] = None) -> Callable:
        """
        You can use task if you want to timing send message. Moreover,
        it will return message after you send message.
        :param msg: the message you want to send
        :param interval: time interval for sending
        :param times: number of executions

        example:
        ----------------------------------------------------------------------
        from cushy_serial import CushySerial, enable_log

        enable_log()
        serial = CushySerial("COM1", 9600)
        instruction = bytes([0x01, 0x06, 0x00, 0x7F, 0x00, 0x01, 0x79, 0xD2])


        @serial.polling_task(msg=instruction, interval=0.5, times=5)
        def handle_rec_msg(rec_msg):
            print(f"[serial] rec polling message: {rec_msg}")
        ----------------------------------------------------------------------
        """
        logger.debug("[cushy-serial] register polling task")

        def decorator(callback: Callable) -> Callable:
            if not self._is_listening:
                self._executor.submit(self._listen_thread)
            if times:
                for i in range(times):
                    self._invoke_polling_task(msg, callback)
                    time.sleep(interval)
            else:
                while True:
                    self._invoke_polling_task(msg, callback)
                    time.sleep(interval)
            return callback

        return decorator

    def _invoke_polling_task(self, msg: str or bytes, callback: Callable):
        self.send(msg)
        callback(self._cur_msg)
        self._cur_msg = None

    def on_message(self):
        """
        listen message from serial and register callback function. It will callback
        when serial receive message from serial.

        example:
        ----------------------------------------------------------------------
        from cushy_serial import CushySerial

        serial = CushySerial("COM1", 9600)
        serial.send("I am python client")


        @serial.on_message()
        def handle_serial_message(msg: bytes):
            str_msg = msg.decode("utf-8")
            print(f"[serial] rec msg: {str_msg}")
        ----------------------------------------------------------------------
        """
        if not self.is_open:
            raise PortNotOpenError()
        if not self._is_listening:
            self._executor.submit(self._listen_thread)

        def decorator(func: Callable):
            self._callbacks.append(func)
            return func

        return decorator

    def _listen_thread(self):
        self._is_listening = True
        self.logger.debug("[cushy-serial] start to listen message")
        while True:
            rec_msg: bytes = self.read_all()
            if rec_msg:
                self.logger.debug(f"[cushy-serial] receive msg: {rec_msg}")
                self._cur_msg = rec_msg
                self._invoke_callbacks(rec_msg)

    def _invoke_callbacks(self, msg: bytes):
        if self._callbacks:
            self.logger.debug("[cushy-serial] run callback task")
        for callback in self._callbacks:
            callback(msg)
            # self._executor.submit(callback, msg)
