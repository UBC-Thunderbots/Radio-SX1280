# File name: sx1280_light.py
#
# Date created: May 15, 2024
#
# Author: Tara Kong
#
# Description: Python library code for SX1280 radio module with Jetson Nano.
#              Originally sourced from sx1280.py but without the unnecessary stuff.
#              Supports LoRa and FLRC mode.

from time import sleep,monotonic
import digitalio
from micropython import const
import adafruit_bus_device.spi_device as spidev
from random import random

# Custom file imports
import sx1280_definitions as constant

# ---------------------------------------------------------
# SX1280 configuration parameters
# ---------------------------------------------------------

_irq1Def = ('RangingSlaveRequestDiscard','RangingMasterResultValid','RangingMasterTimeout','RangingMasterRequestValid','CadDone','CadDetected','RxTxTimeout','PreambleDetected')
_irq2Def = ('TxDone','RxDone','SyncWordValid','SyncWordError','HeaderValid','HeaderError','CrcError','RangingSlaveResponseDone')

# These were defined by the library - don't touch unless you know what you're doing.
_mode_mask = const(0xE0)
_cmd_stat_mask = const(0x1C)


# ---------------------------------------------------------
# SX1280 source code
# ---------------------------------------------------------

class SX1280:
    # _status, _status_msg, _status_mode, and _status_cmd were all defined by the original library.
    _status=bytearray(1)
    _status_msg = {
            'mode': '',
            'cmd' : '',
            'busy': False }

    _status_mode = {
            0:'N/A',
            1:'N/A',
            2:'STDBY_RC',
            3:'STDBY_XOSC',
            4:'FS',
            5:'Rx',
            6:'Tx'
        }

    _status_cmd = {
            0:'N/A',
            1:'Cmd Successful',
            2:'Data Available',
            3:'Timed-out',
            4:'Cmd Error',
            5:'Failure to Execute Cmd',
            6:'Tx Done' }

    # The maximum buffer size needed is the maximum payload length, plus the number of bytes that the payload is offset in the buffer.
    _BUFFER = bytearray(constant.RXBUFFER_SIZE + constant.RXBUFFER_OFFSET)

    # LoRa: Not used.
    _packetParamsLoRa = {
        'PreambleLength': 12,
        'HeaderType'    : constant.PACKET_HEADER_EXPLICIT,
        'PayloadLength' : 11,
        'CrcMode'       : constant.PACKET_CRC_MODE_ON,
        'InvertIQ'      : constant.PACKET_IQ_NORMAL
    }

    # LoRa: Not used.
    _modParamsLoRa = {
        'modParam1': constant.LORA_SF7,
        'modParam2': constant.LORA_BW_0400,
        'modParam3': constant.LORA_CR_4_5
    }

    # FLRC params: don't change unless you know what you're doing - these params are what Tiger uses.
    _packetParamsFLRC = {
        'PreambleLength': constant.PREAMBLE_LENGTH_16_BITS,
        'SyncWordLength': constant.FLRC_SYNC_WORD_LEN_P32S,
        'SyncWordMatch' : constant.RADIO_RX_MATCH_SYNCWORD_1,
        'PayloadType'   : constant.RADIO_PACKET_VARIABLE_LENGTH,
        'PayloadLength' : constant.RXBUFFER_SIZE,
        'CrcMode'       : constant.RADIO_CRC_OFF,
        'Whitening'     : constant.RADIO_WHITENING_OFF
    }

    # FLRC params: don't change unless you know what you're doing - these params are what Tiger uses.
    _modParamsFLRC = {
        'modParam1': constant.FLRC_BR_1_300_BW_1_2,
        'modParam2': constant.FLRC_CR_1_0,
        'modParam3': constant.RADIO_MOD_SHAPING_BT_1_0
    }


    def __init__(self, spi, cs, reset, busy, dio, frequency, *, baudrate=constant.LT_SPEED_MAXIMUM, debug=True, txen=False, rxen=False):
        self._device = spidev.SPIDevice(spi, cs, baudrate=baudrate, polarity=0, phase=0)
        self._reset = reset
        self._reset.switch_to_input(pull=digitalio.Pull.UP)
        self._busy = busy
        self._busy.switch_to_input()
        self._debug = debug
        self._defaultDio = dio

        # default packet type LoRa
        self._packetType = 0

        self._txen = txen
        self._rxen = rxen

        self._frequency = frequency

        self.reset()
        self._busywait()
        self.timeouts = 0

        # TODO: Not used; only used in receive_mod().
        self.ack_delay = None

        # TODO: Not used; only used in send_mod().
        # RH Header Bytes
        self.node = constant.RH_BROADCAST_ADDRESS
        self.destination = constant.RH_BROADCAST_ADDRESS
        self.identifier = 0
        self.flags = 0

        self.configureFLRC()


    def configureFLRC(self):
        '''
        Most of these settings are copied from Tiger and the ESP32 FLRC receive code, excluding the items marked "TODO".
        '''
        self._sleeping=False
        self._setRanging = False
        self._ranging=False
        self._status = 0
        self._autoFS=False
        self._listen=False
        self._rangeListening=False
        
        self.setStandby(constant.MODE_STDBY_XOSC)
        self.setRegulatorMode(constant.USE_DCDC)
        self.setPacketType(constant.PACKET_TYPE_FLRC)
        self.frequencyGhz=self._frequency

        # Use default rx base address
        self.setBufferBaseAddress(rxBaseAddress=0x00)

        self.setModulationParams(
            self._modParamsFLRC['modParam1'], self._modParamsFLRC['modParam2'], self._modParamsFLRC['modParam3']
        )
        self.setPacketParams(constant.PACKET_TYPE_FLRC)

        self.setDioIrqParams( irqMask=constant.IRQ_RADIO_ALL, dio1Mask=[0x40,0x02], dio2Mask=[0x00,0x00], dio3Mask=[0x00,0x00]  )

        self.setSyncWord1(constant.FLRC_SYNCWORD)
        self.setSyncWordErrorTolerance(constant.FLRC_SYNCWORD_TOLERANCE)
        self.setAutoFs(True)
        self.setFs()

        self.clearIrqStatus()
        
        self.setFLRCPayloadLengthReg(constant.RXBUFFER_SIZE)

        # TODO: Not used.
        # Disable Advanced Ranging
        self._sendCommand(bytes([0x9A,0]))

        # TODO: Not used.
        # Set Save Context
        self._sendCommand(bytes([0xD5]))

        if self._debug: print("Radio Initialized - FLRC Mode") 


    def configureLoRa(self):
        self._sleeping=False
        self._setRanging = False
        self._ranging=False
        self._status = 0
        self._autoFS=False
        self._listen=False
        self._rangeListening=False
        self.setStandby(constant.MODE_STDBY_RC)
        self.setRegulatorMode(constant.USE_LDO)
        self.setPacketType(constant.PACKET_TYPE_LORA)
        self.frequencyGhz=self._frequency
        self.setBufferBaseAddress(rxBaseAddress=0x80)
        self.setModulationParams(
            self._modParamsLoRa['modParam1'], self._modParamsLoRa['modParam2'], self._modParamsLoRa['modParam3']
        )
        self.setPacketParams(constant.PACKET_TYPE_LORA)
        self.setDioIrqParams()
        self.setHighSensitivityLna(False) # changed to shut off May 6
        self.clearIrqStatus()

        # Disable Advanced Ranging
        self._sendCommand(bytes([0x9A,0]))

        # Set Save Context
        self._sendCommand(bytes([0xD5]))

        if self._debug: print("Radio Initialized - LoRa Mode") 


    def _convertStatus(self, status):
        mode = (status & _mode_mask)>>5
        cmdstat = (status & _cmd_stat_mask)>>2
        if mode in self._status_mode:
            self._status_msg['mode']=self._status_mode[mode]
        if cmdstat in self._status_cmd:
            self._status_msg['cmd']=self._status_cmd[cmdstat]
        self._status_msg['busy'] = not bool(status & 0x1)
        return self._status_msg


    def _sendCommand(self, command, stat=True):
        '''
        Send a command to the SX1280 radio module.
        '''
        rxbuffer = bytearray(140)
        if self._debug:
            print("_sendCommand()")
        _size=len(command)
        self._busywait()
        print(f"_size: {_size}")
        with self._device as spi:
            print(f"command: {command}")
            spi.write_readinto(command, self._BUFFER, out_end=_size, in_end=_size)
        if stat:
            print("\tcommand:",[hex(i) for i in command])
        if self._debug:
            print("\tstatus:", "{}".format(self._convertStatus(self._BUFFER[0])))
        
        self._busywait()
        return self._BUFFER[:_size]


    def writeRegister(self, address1, address2, data=[]):
        '''
        args: data is a list of bytes, but not a bytes() object
        '''
        if self._debug:
            print("Writing to:", hex(address1), hex(address2))
        
        print(i for i in data)
        self._sendCommand( bytes( [constant.RADIO_WRITE_REGISTER, address1, address2] + data ) )


    # TODO: Not used by FLRC, not tested; only used by setHighSensitivity
    # DO NOT USE THIS METHOD, I was playing around with things and it's currently in a broken state.
    # To read registers, use the function readRegisters() instead.
    def readRegister(self, address1, address2):
        '''
        The read operation is as follows:
        WRITE: [ command  |  address1  |  address2  |  0x00    |  0x00         |  0x00,           ]
        READ:  [ status   |  status    |  status    |  status  |  data@address |  data@address+1  ]

        So, we write 3 bytes [command, address1, address2] while ignoring the returned bytes;
        then read 3 more bytes [status, data@address, data@address+1] into self._BUFFER
        
        The data we want is contained in self._BUFFER[3:end]
        '''

        if self._debug:
            print("Reading:", hex(address1), hex(address2))
        self._busywait()

        # Send an array of nops after the readCommand, to read back the contents of RXBUFFER
        # todo: determine how many nops to send (payloadLen, or payloadLen + 1?)
        numBytesToRead = 5
        nops = [0xFF for i in range(numBytesToRead)]
        print(len(nops))

        responseBufferOffset = 3

        # The readRegister command begins returning its response <insert offset> clock cycles after the command is sent.
        self._sendCommand(bytes( [constant.RADIO_READ_REGISTER, address1, address2] + nops ) )

        rxBuffer = self._BUFFER[responseBufferOffset : responseBufferOffset + numBytesToRead]
            # spi.write(bytes([constant.RADIO_READ_REGISTER,address1,address2]), end=3)
            # spi.readinto(self._BUFFER, end=3) # todo: this might be wrong, changed from 2 to 3
        if self._debug:
            [print(hex(i), ' ', end='') for i in self._BUFFER]
            print()
        self._busywait()
        return self._BUFFER[1:3]


    def readRegisters(self, address1, address2, _length=1):
        '''
        read_reg_cmd,   addr[15:8],     addr[7:0],   NOP,    NOP,    NOP,    NOP,  ...
            status        status         status     status  data1   data2   data3  ...
        '''
        _size = _length + 4
        if self._debug: print("Reading:", hex(address1),hex(address2))
        self._busywait()
        with self._device as spi:
            spi.write_readinto(
                bytes( [constant.RADIO_READ_REGISTER, address1, address2, 0] + [0] * _length ),
                self._BUFFER,
                out_end=_size,
                in_end=_size
            )
        self._busywait()
        if self._debug: print("Read Regs ({}, {}) _BUFFER: {}".format(hex(address1),hex(address2),[hex(i) for i in self._BUFFER[4:_size]]))
        return self._BUFFER[4:_size]


    # TODO: Not used, not tested.
    def printRegisters(self, start=0x0900, stop=0x09FF, p=True):
        _length=stop-start+1
        _size=_length+4
        buff=bytearray(_size)
        self._busywait()
        with self._device as spi:
            spi.write_readinto(bytes([constant.RADIO_READ_REGISTER])+int(start).to_bytes(2,'big')+b'\x00'+b'\x00'*_length,buff,out_end=_size,in_end=_size)
        if p:
            pass
        else:
            return buff


    # @timeout(3)
    def _busywait(self):
        _t = monotonic() + 3
        while monotonic() < _t:
            if not self._busy.value:
                return True
        print("TIMEOUT on _busywait.")
        self.timeouts += 1
        if self.timeouts > 5:
            self.timeouts = 0
            try:
                with open('/sd/log.txt','a') as f:
                    f.write('sb:{}\n'.format(int(monotonic())))
            except: pass
            self._resetIo()
        if hasattr(self, 'timeout_handler'):
            self.timeout_handler()
        return False


    def _resetIo(self):
        self._reset.switch_to_output(value=False)
        self._busy.switch_to_input()
        sleep(5)
        self._reset.switch_to_input(pull=digitalio.Pull.UP)
        sleep(2)
        self.configureLoRa()


    # TODO: Not used, not tested; only used by send_mod().
    def _waitForIrq(self):
        if self._defaultDio:
            return self._dioWait(self._defaultDio)
        else:
            return self.IRQwait(bit=1)


    # TODO: Not used, not tested; only used by _waitForIrq().
    # @timeout(3)
    def _dioWait(self, pin):
        _t=monotonic()+3
        while monotonic()<_t:
            if pin.value:
                self.clearIrqStatus()
                return True
        print("TIMEDOUT on _dioWait.")
        if hasattr(self, 'timeout_handler'):
            self.timeout_handler()
        return False


    # TODO: Not used, not tested; only used by _waitForIrq().
    # @timeout(4)
    def IRQwait(self, bit):
        _t=monotonic()+4
        while monotonic()<_t:
            _irq=self.getIrqStatus(clear=False)[1] & 1
            # print(hex(_irq))
            if (_irq >> bit) & 1:
                return True
        print("TIMEDOUT on IRQwait.")
        if hasattr(self, 'timeout_handler'):
            self.timeout_handler()
        return False


    def setRegulatorMode(self, mode): # changed default mode to LDO
        if self._debug:
            print("Setting Regulator Mode.")
        self._sendCommand(bytes([constant.RADIO_SET_REGULATORMODE, mode]))


    def reset(self):
        self._reset.switch_to_output(value=False)
        sleep(0.05)  # 50 ms
        self._reset.switch_to_input(pull=digitalio.Pull.UP)
        sleep(0.03)  # 30 ms


    def setStandby(self, state):
        '''
        MODE_STDBY_XOSC or MODE_STDBY_RC
        '''
        if self._debug: print("Setting Standby.")
        self._sendCommand(bytes([constant.RADIO_SET_STANDBY, state]))


    def sleep(self):
        self._busywait()
        with self._device as spi:
            spi.write_readinto(bytes([constant.RADIO_SET_SLEEP, 0x07]),self._BUFFER,out_end=2,in_end=2)
        self._sleeping=True
        if self._debug:
            print("\t\tSleeping SX1280.")
            print("\t\t{}".format(self._convertStatus(self._BUFFER[0])))


    # TODO: Not used, not tested.
    def wakeUp(self):
        if self._sleeping:
            if self._debug:
                print("\t\tWaking SX1280.")
            with self._device as spi:
                sleep(0.1)
                # Send no-op to wake-up
                spi.write(bytes([0xC0,0]))
            if not self._busywait():
                print("wakeUp busy fail.")
            # Reconfigure the SX1280.
            if self._packetType == constant.PACKET_TYPE_LORA:
                self.configureLoRa()
            elif self._packetType == constant.PACKET_TYPE_FLRC:
                self.configureFLRC()


    def setPacketType(self, packetType):
        if self._debug:
            print("Setting Packet Type.")
        self._sendCommand(bytes([constant.RADIO_SET_PACKETTYPE, packetType]))
        self._packetType = packetType


    @property
    def frequencyGhz(self):
        return float(str(self._frequency) + "E" + "9")


    @frequencyGhz.setter
    def frequencyGhz(self, freq):
        '''
        0xB89D89 = 12098953 PLL steps = 2.4 GHz
        2.4 GHz  = 12098953*(52000000/(2**18))
        '''
        self._frequency=freq
        _f=int(float(str(freq)+"E"+"9")/constant.FREQ_STEP)
        if self._debug: print("\tSX1280 freq: {:G} GHz ({} PLL steps).".format(float(str(freq)),_f))
        
        freq_buffer = []
        freq_buffer.append( (_f >> 16) & 0xFF )
        freq_buffer.append(( _f >> 8) & 0xFF )
        freq_buffer.append( _f & 0xFF )
        
        self._sendCommand(bytes([constant.RADIO_SET_RFFREQUENCY, freq_buffer[0], freq_buffer[1], freq_buffer[2]]))


    def setBufferBaseAddress(self, txBaseAddress=0x00, rxBaseAddress=0x00):
        if self._debug:
            print("Setting Buffer Base Address.")
        self._txBaseAddress = txBaseAddress
        self._rxBaseAddress = rxBaseAddress
        self._sendCommand(bytes([constant.RADIO_SET_BUFFERBASEADDRESS, txBaseAddress, rxBaseAddress]))


    def setModulationParams(self, modParam1, modParam2, modParam3):
        # LoRa with SF7, (BW1600=0x0A -> changed to BW400=0x26), CR 4/5
        # Must set PacketType first! - See Table 13-48,49,50
        if self._debug:
            print("Setting Modulation Parameters.")

        self._sendCommand(bytes([constant.RADIO_SET_MODULATIONPARAMS, modParam1, modParam2, modParam3]))
        
        # implement data sheet additions, datasheet SX1280-1_V3.2section 14.47
        if self._packetType == constant.PACKET_TYPE_LORA:
            self._busywait()

            # if (modParam1 == constant.LORA_SF5) or (modParam1 == constant.LORA_SF6):
            #     self.writeRegister(0x09, 0x25, 0x1E)

            if (modParam1 == constant.LORA_SF7): # or (modParam1 == _LORA_SF8):
                self.writeRegister(0x09, 0x25, 0x37)

            # elif ( (modParam1 == _LORA_SF9) or (modParam1 == _LORA_SF10) or 
            #     (modParam1 == _LORA_SF11) or (modParam1 == _LORA_SF12) ):
            #     self.writeRegister(0x09, 0x25, 0x32)

            else:
                print(f"Invalid Spreading Factor: {modParam1}.")


    def setPacketParams(self, packet_type):
        '''
        Set the packet parameters.
        '''

        if self._debug:
            print("Setting Packet Parameters.")

        packet_params = []

        if packet_type == constant.PACKET_TYPE_LORA:
            if self._debug:
                print(self._packetParamsLoRa)

            packet_params = [
                self._packetParamsLoRa['PreambleLength'],
                self._packetParamsLoRa['HeaderType'],
                self._packetParamsLoRa['PayloadLength'],
                self._packetParamsLoRa['CrcMode' ],
                self._packetParamsLoRa['InvertIQ'],
                0x00,
                0x00
            ]
        elif packet_type == constant.PACKET_TYPE_FLRC:
            if self._debug:
                print(self._packetParamsFLRC)
                
            packet_params = [
                self._packetParamsFLRC['PreambleLength'],
                self._packetParamsFLRC['SyncWordLength'],
                self._packetParamsFLRC['SyncWordMatch'],
                self._packetParamsFLRC['PayloadType' ],
                self._packetParamsFLRC['PayloadLength'],
                self._packetParamsFLRC['CrcMode' ],
                self._packetParamsFLRC['Whitening']
            ]
        else:
            print(f"Error: Invalid packet type: {packet_type}.")
            return

        self._sendCommand(
            bytes( [constant.RADIO_SET_PACKETPARAMS] + packet_params )
        )


    def setTxParams(self, power=0x1C, rampTime=0x00):
        # power=10 dBm (0x1C), rampTime=2us (0x00). See Table 11-47
        # P=-18+power -18+0x1C=10
        if self._debug:
            print("Setting Tx Parameters.")
        self._sendCommand(bytes([constant.RADIO_SET_TXPARAMS,power,rampTime]))


    def writeBuffer(self, data):
        #Offset will correspond to txBaseAddress in normal operation.
        _offset = self._txBaseAddress
        _len = len(data)
        assert 0 < _len <= 252
        self._busywait()
        with self._device as spi:
            spi.write(bytes([constant.RADIO_WRITE_BUFFER,_offset])+data,end=_len+2)


    def readBuffer(self, offset, payloadLen):
        '''
        The readBuffer SPI data transfer operation is as follows, for n=payloadLen:
        DATA OUT: [ Opcode = 0x1B  |  offset  |   NOP    |     NOP       |      NOP        | ... |        NOP          ]
        DATA IN:  [     status     |  status  |  status  |  data@offset  |  data@offset+1  | ... |  data@offset+(n-3)  ]

        To receive the data from the rxBuffer, we need to transmit an array of NOPs immediately after sending the readBuffer command.
        
        Note that we need to transmit one extra byte than the actual payload length due to the 1-byte gap between the transmitted bytes and received bytes (see SX1280 user manual, Section 11.4.2 about the ReadBuffer command)
        
        The data we want is contained in self._BUFFER[constant.RXBUFFER_OFFSET:end]
        '''
        if self._debug:
            print(f"Reading the receive buffer. The payload length is {payloadLen} bytes.")
        
        # Make sure the radio is not busy.
        self._busywait()

        # Initialize the array of NOPs to send after the readBuffer command.
        nops = [0x00 for i in range(payloadLen + 1)]
        self._sendCommand(bytes([constant.RADIO_READ_BUFFER, offset] + nops))

        # The payload data begins at an offset of constant.RXBUFFER_OFFSET bytes in the buffer.
        rxBuffer = self._BUFFER[constant.RXBUFFER_OFFSET : constant.RXBUFFER_OFFSET + payloadLen]

        return rxBuffer


    def setDioIrqParams(self, irqMask=constant.IRQ_RADIO_ALL, dio1Mask=[0x00, 0x00], dio2Mask=[0x00, 0x00], dio3Mask=[0x00, 0x00]):
        '''
        Enable interrupts on specified DIO pins.
        '''
        if self._debug:
            print("Setting DIO IRQ Parameters.")
        self._sendCommand( bytes( [constant.RADIO_SET_DIOIRQPARAMS] + irqMask + dio1Mask + dio2Mask + dio3Mask ) )


    def clearIrqStatus(self, irqMask=constant.IRQ_RADIO_ALL):
        if self._debug: print("Clearing IRQ Status.")
        self._sendCommand( bytes( [constant.RADIO_CLR_IRQSTATUS] + irqMask ) )
        self.getIrqStatus()


    def getIrqStatus(self, clear=[0xFF,0xFF], parse=True, debug=True):
        if self._debug: print("Getting IRQ Status.")
        _, _, _irq1,_irq2 = self._sendCommand( bytes( [constant.RADIO_GET_IRQSTATUS, 0x00, 0x00, 0x00] ) )

        if parse:
            if debug:
                print("\tIRQ[15:8]:{}, IRQ[7:0]:{}".format(hex(_irq1),hex(_irq2)))

            _rslt=[]

            for i,j in zip(reversed('{:08b}'.format(_irq1)),_irq1Def): # [15:8]
                if int(i):
                    _rslt.append(j)

            for i,j in zip(reversed('{:08b}'.format(_irq2)),_irq2Def): # [7:0]
                if int(i):
                    _rslt.append(j)

            if self._debug:
                print("\tIRQ Results: {}".format(_rslt))

            return((_rslt,hex(_irq1),hex(_irq2)))

        if clear:
            if clear==True:
                clear=[0xFF,0xFF]

            self._sendCommand(bytes([constant.RADIO_CLR_IRQSTATUS]+clear)) # clear IRQ status

        return (_irq1,_irq2)


    def setTx(self, timeoutTx=constant.TIMEOUT_0_S):
        # Activate transmit mode with no timeout. Tx mode will stop after first packet sent.
        if self._debug:
            print("Setting Tx.")

        self.clearIrqStatus()
        self._sendCommand(bytes([constant.RADIO_SET_TX, constant.PERIODBASE_01_MS] + timeoutTx))
        self._listen=False


    def setRx(self, timeoutRx=constant.TIMEOUT_60_S):
        '''
        timeoutRx = 16 bit parameter of how many steps to time-out
        see Table 11-22 for pBase values (0xFFFF=continuous, 0xEA60=60s timeout, or 60000ms)
        Time-out duration = pBase * periodBaseCount
        '''
        if self._debug:
            print("Setting Rx." )

        if self._rxen:
            self._txen.value=False
            self._rxen.value=True

        self.clearIrqStatus()
        self._sendCommand(bytes([constant.RADIO_SET_RX, constant.PERIODBASE_01_MS] + timeoutRx))


    def setFs(self):
        self._sendCommand(bytes([constant.RADIO_SET_FS]))


    def setAutoFs(self, value):
        '''
        args: bool value
        '''
        self._sendCommand(bytes([constant.RADIO_SET_AUTOFS, value]))
        self._autoFS=value


    def setHighSensitivityLna(self, enabled=True):
        _regUpper, _ = self.readRegister(0x8,0x91)

        if enabled:
            self.writeRegister( 0x8,0x91, [_regUpper | 0xC0] )
        else:
            self.writeRegister( 0x8, 0x91, [_regUpper & 0x3F] )


    def getPacketStatus(self):
        # See Table 11-63
        # self._packet_status = []
        packetStatus = self._sendCommand(bytes([constant.RADIO_GET_PACKETSTATUS, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
        # [print(hex(i)+' ',end='') for i in self._BUFFER[:6]]

        self.rssiSync = int(-1*(packetStatus[2])/2)
        self.snr = int((packetStatus[3])/4)

        return (self.rssiSync, self.snr)


    def getRxBufferStatus(self):
        _, _, rxPayloadLength, rxStartBufferPointer = self._sendCommand(bytes([constant.RADIO_GET_RXBUFFERSTATUS,0x00,0x00,0x00]))
        
        return [rxPayloadLength, rxStartBufferPointer]


    # TODO: Not used, not tested.
    def send(self, data, pin=None, irq=False, header=True, ID=0, target=0, action=0, keep_listening=False):
        """Send a string of data using the transmitter.
           You can only send 252 bytes at a time
           (limited by chip's FIFO size and appended headers).
        """
        return self.send_mod(data,keep_listening=keep_listening,header=header)


    # TODO: Not used.
    @property
    def listen(self):
        return self._listen


    # TODO: Not used.
    @listen.setter
    def listen(self, enable):
        if enable:
            if not self._listen:
                if self._rxen: 
                    self._txen.value=False
                    self._rxen.value=True
                self.setRx()
                self._listen = True
        else:
            if self._rxen: 
                self._rxen.value=False
            self.setStandby(_MODE_STDBY_RC)
            self._listen = False


    def receive(self, timeoutSeconds=15):
        """Receive and parse a packet via the SX1280 transceiver.

           For FLRC, there is a payload size limit of 127 bytes.
        """
        if not self._defaultDio:
            print("Must set default DIO pin!")
            return False

        self.setRx()

        timedOut = False
        start = monotonic()
        
        # Block until timeout occurs or DIO goes high.
        while not timedOut and not self._defaultDio.value:
            if (monotonic() - start) >= timeoutSeconds:
                timedOut = True

        # Radio has received something.

        # Initialize packet.
        packet = None
        self.setStandby(constant.MODE_STDBY_RC)

        if not timedOut:
            print("Payload received!")
            if self._debug:
                self.getIrqStatus()

            self._rxBufferStatus = self.getRxBufferStatus()
            self._packetLength = self._rxBufferStatus[0]
            self._packetPointer = self._rxBufferStatus[1]

            if self._packetLength > 0:
                if self._debug:
                    print(f"Offset: {self._packetPointer}; Length: {self._packetLength}")
                
                packet = self.readBuffer(offset=self._packetPointer, payloadLen=self._packetLength)
                
                if self._debug:
                    self.getIrqStatus()

        return packet


    @property
    def getPacketInfo(self):
        return (self._packetLength, self._packetPointer)


    def getRssi(self, raw=False):
        self._rssi = self._sendCommand(bytes([constant.RADIO_GET_PACKETSTATUS,0x00,0x00]))
        if raw:
            return self._rssi[-1]
        else:
            return -1*self._rssi[-1]/2 # dBm


    def getStatus(self, raw=False):
        self._busywait()
        with self._device as spi:
            spi.write_readinto(bytes([constant.RADIO_GET_STATUS]),self._BUFFER,out_end=1,in_end=1)

        if raw:
            return self._BUFFER[0]
        self._busywait()
        return self._convertStatus(self._BUFFER[0])


    # TODO: Not used, not tested; only used in receive_mod() and send()
    def send_mod(self, data, *, keep_listening=False, header=False, destination=None, node=None, identifier=None, flags=None, debug=False):
        data_len = len(data)
        assert 0 < data_len <= 252
        if self._txen:
            self._rxen.value=False
            self._txen.value=True
            if debug:
                print("\t\ttxen:on, rxen:off.")
        if header:
            payload = bytearray(4)
            if destination is None:  # use attribute
                payload[0] = self.destination
            else:  # use kwarg
                payload[0] = destination
            if node is None:  # use attribute
                payload[1] = self.node
            else:  # use kwarg
                payload[1] = node
            if identifier is None:  # use attribute
                payload[2] = self.identifier
            else:  # use kwarg
                payload[2] = identifier
            if flags is None:  # use attribute
                payload[3] = self.flags
            else:  # use kwarg
                payload[3] = flags
            if debug: print("HEADER: {}".format([hex(i) for i in payload]))
            data = payload + data
            data_len+=4
        # Configure Packet Length
        self._packetParamsLoRa['PayloadLength']=data_len
        self.setPacketParams(PACKET_TYPE_LORA)
        self.writeBuffer(data)
        self.setTx()
        txdone=self._waitForIrq()
        if keep_listening:
            self.listen=True
        else:
            if self._txen:
                self._txen.value=False
                if debug: print("\t\ttxen:off, rxen:n/a.")
        return txdone


    # TODO: Not used, not tested. Likely that it's currently broken.
    def receive_mod(self, *, keep_listening=True, with_header=False, with_ack=False, timeout=15,debug=True):
        timedOut = False
        if not self._defaultDio:
            print("Must set default DIO pin!")
            return False
        if timeout is not None:
            # if not self._listen:
            self.listen = True
            start = monotonic()
            timedOut = False
            # Blocking wait for interrupt on DIO
            while not timedOut and not self._defaultDio.value:
                if (monotonic() - start) >= timeout:
                    timedOut = True
        # Radio has received something!
        packet = None
        # Stop receiving other packets
        self.listen=False
        if not timedOut:

            regData = self.getIrqStatus()

            # print("IRQ status registers:", bin(regData), bin(reg_lower))

            # if (regData & IRQ_HEADER_ERROR) | (regData & IRQ_CRC_ERROR) | (regData & IRQ_RX_TX_TIMEOUT ) | (regData & IRQ_SYNCWORD_ERROR ): #check if any of the preceding IRQs is set
            #     return 0 # packet is errored somewhere so return 0

            self._rxBufferStatus = self.getRxBufferStatus()
            self._packetLength = self._rxBufferStatus[0]
            self._packetPointer = self._rxBufferStatus[1]
            if self._debug:
                print(f"Offset: {self._packetPointer}; Length: {self._packetLength}")
            if self._packetLength > 0:
                packet = self.readBuffer(offset=self._packetPointer,payloadLen=self._packetLength+1)[1:]
            self.clearIrqStatus()
            if self._packetLength > 4:
                if (self.node != _RH_BROADCAST_ADDRESS
                    and packet[0] != _RH_BROADCAST_ADDRESS
                    and packet[0] != self.node):
                    if debug: print("Overheard packet:", packet)
                    packet = None
                # send ACK unless this was an ACK or a broadcast
                elif (with_ack
                    and ((packet[3] & _RH_FLAGS_ACK) == 0)
                    and (packet[0] != _RH_BROADCAST_ADDRESS)):
                    # delay before sending Ack to give receiver a chance to get ready
                    if self.ack_delay is not None:
                        sleep(self.ack_delay)
                    self.send_mod(
                        b"!",
                        keep_listening=keep_listening,
                        header=True,
                        destination=packet[1],
                        node=packet[0],
                        identifier=packet[2],
                        flags=(packet[3] | _RH_FLAGS_ACK))
                    # print("sband ack to {}".format(packet[1]))
                # if not with_header:  # skip the header if not wanted
                #     packet = packet[4:]
        # Listen again if necessary and return the result packet.
        if keep_listening:
            self.listen=True
        return packet


    def setFLRCPayloadLengthReg(self, length):
        '''
        Set the payload length for the FLRC packet type
        '''
        if self._debug:
            print("Setting FLRC Payload Length Register.")
        self.writeRegister(constant.REG_LR_FLRCPAYLOADLENGTH[0], constant.REG_LR_FLRCPAYLOADLENGTH[1], [length])


    def setSyncWord1(self, syncWord):
        '''
        Set syncWord1 for the FLRC packet type
        '''
        if self._debug:
            print(f"Setting SyncWord1: {hex(syncWord)}.")

        syncWordBaseAddress = constant.REG_FLRCSYNCWORD1_BASEADDR

        # Extract the individual sync word address bytes
        syncWordBaseAddress_bytes = self.getBytesFromAddress( syncWordBaseAddress )
        
        # Extract the individual bytes of the sync word
        syncWord_bytes = [
            ( syncWord >> 24 ) & 0xFF,
            ( syncWord >> 16 ) & 0xFF,
            ( syncWord >> 8 ) & 0xFF,
            ( syncWord ) & 0xFF
        ]

        # Print the sync word.
        for i in syncWord_bytes:
            print( hex(i) )

        # Write the sync word to the register, starting from the base address.
        self.writeRegister( syncWordBaseAddress_bytes[0], syncWordBaseAddress_bytes[1], syncWord_bytes )
    
        print("Wrote sync word.")

        # Read the registers to make sure the sync word was set correctly.
        self.readRegisters(syncWordBaseAddress_bytes[0], syncWordBaseAddress_bytes[1], _length=4)


    def setSyncWordErrorTolerance(self, numErrsAllowed):
        '''
        Sets how many sync word errors are allowed before a SyncWordError fault is triggered
        Note: This register was not defined in the datasheet, taken from Stuarts project open source library

        The error tolerance is stored in register address 0x09CD, in the lower byte (i.e. bits [7:0])
        '''
        if self._debug:
            print("Setting the Sync Word Error Tolerance.")

        regs = self.readRegisters(0x09, 0xCD)
        print(f"reading syncWordErrorTolerance registers: {regs}")
        dataUpper = regs[0] & 0xF0
        dataLower = numErrsAllowed & 0x0F

        print(dataLower)

        self.writeRegister( 0x09, 0xCD, [dataUpper | dataLower] )
        self.readRegisters(0x09, 0xCD)

    def getBytesFromAddress(self, address):
        '''
        Extracts the upper and lower byte from a register address

        For example, given address 0x09CF, returns [0x09, 0xCF].
        
        This makes it easier to use the library functions which write one byte at a time.
        '''
        upper = (address >> 8) & 0xFF
        lower = address & 0XFF

        return [upper, lower]
