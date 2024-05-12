# adafruit-blinka library

import board
import busio
import digitalio
from time import sleep

import sx1280

# NAME    PIN #    LABEL    ALT FUNCTION
# -----------------------------------
# CS0     24       D8
# SCLK    23       D11      SPI1_SCK
# MOSI    19       D10      SPI1_MOSI
# MISO    21       D9       SPI1_MISO
# RESET   38       D20
# BUSY    40       D21
# DIO2    7        D4

 
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
print("configured spi")

# don't need to specify chip select, SPI1 will always pull down CS0
#CS = digitalio.DigitalInOut(board.D8)
#print("configured CS pin")

# configure RESET - pin 38
RESET = digitalio.DigitalInOut(board.D20)
print("configured RESET pin")
BUSY = digitalio.DigitalInOut(board.D21)
print("configured BUSY pin")

# configure DIO1 - pin 7
DIO2 = digitalio.DigitalInOut(board.D4)

# None cs for now since it already uses the CS0 default
radio = sx1280.SX1280(spi, None, RESET, BUSY, DIO2, 2.445)

print("Configured the radio")
print()
print()

# Prepare radio for Rx
radio.listen = True

while True:
    sleep(1)
    print("Waiting for message...")
    # msg = radio.receive_mod()
    payload = radio.receive()
    if payload != None:
        payloadLen = len(payload)
        print(payload)
        # print(radio.packet_status)
        # sleep(1)
