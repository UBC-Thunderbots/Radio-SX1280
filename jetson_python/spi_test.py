# SPDX-FileCopyrightText: 2021 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
import time
import board
import busio
import digitalio

#CS = digitalio.DigitalInOut(board.D8)
#CS.switch_to_output()
#CS.value = True

spi = busio.SPI(board.SCLK, board.MOSI, board.MISO)
while not spi.try_lock():
    pass
spi.configure(baudrate=100000)
# spi.unlock()

msg = "hi"
nums = [1,1,1,1]
bites = bytearray(nums)
print(bites)
bites_read = bytearray(4)

while True:
#    CS.value = False
    spi.write_readinto(bites, bites_read)
#    CS.value = True

    time.sleep(0.5)
