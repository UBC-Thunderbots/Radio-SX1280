## README

### Setup and dependencies
#### Useful links and tutorials
- SX1280 user manual: https://www.tme.eu/Document/1042f35a88b6ee421559d19923804032/SX128x.pdf
- Stuart's Library Github repo, for setting up the ESP32: https://github.com/StuartsProjects/SX12XX-LoRa
- CircuitPython SX1280 library, for setting up the Jetson: https://github.com/maholli/CircuitPython_SX1280
    - Note that this library was very bare bones and only supported LoRa (and not even properly) so take this with a grain of salt; however, it might still be useful since I based this FLRC implementation partially off of this library.
- Tutorial: CircuitPython on the Jetson Nano: https://learn.adafruit.com/circuitpython-libraries-on-linux-and-the-nvidia-jetson-nano

#### Libraries needed to install or other dependencies
- Adafruit_blinka: https://github.com/adafruit/Adafruit_Blinka
- Adafruit_bus_device: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
- and possibly others that I forgot, but either CircuitPython tutorial will mention it or it will become apparent when things don't build XD
- I had to update Python on the Jetson - 3.8 or higher should work.

### Running this project
#### Files to care about:
- The execution script is receive.py
- The sx1280 library that receive.py uses is 'sx1280_light.py'
    - I created this file based off of 'sx1280.py', but cut out almost all of the irrelevant stuff and added support for FLRC.
    - There are comments throughout the file, indicating files that aren't in use, haven't been tested, parameters that should/should not be modified, etc.
- Constants are stored in sx1280_definitions.py
- You can ignore spi_test.py - it's outdated and not being used.

#### Other notes
- I had to run this using SPI0 but we'll need to switch to SPI1 for the actual thing
- There are constraints on the payload size and receiving won't just cut off the payload if you violate them, it'll return somewhat convincing garbage - I found this out the hard way so don't do this
    - MINIMUM = 6 bytes
    - MAXIMUM = 127 bytes

### Other troubleshooting
When in doubt, make sure to check all the connections and then double and triple check them. Also make sure all the wires are still soldered correctly. The amount of time I wasted just because these issues...

#### GPIO 0 and 1 permissions
I had to override chown each time I booted the Jetson to access gpio0 and gpio1 (I think because I wasn't root user)

https://github.com/NVIDIA/jetson-gpio/issues/20
To temporarily fix (need to run every time the jetson reboots):
- sudo usermod -aG gpio $USER
- sudo chown root.gpio /dev/gpiochip1
- sudo chmod 660 /dev/gpiochip1