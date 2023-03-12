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

from cushy_serial import CushySerial, enable_log

enable_log()
serial = CushySerial("COM1", 9600)
instruction = bytes([0x01, 0x06, 0x00, 0x7F, 0x00, 0x01, 0x79, 0xD2])


@serial.polling_task(msg=instruction, interval=0.5, times=5)
def handle_rec_msg(rec_msg):
    print(f"[serial] rec polling message: {rec_msg}")
