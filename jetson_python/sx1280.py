from time import sleep,monotonic
import digitalio
from micropython import const
import adafruit_bus_device.spi_device as spidev
from random import random

#SPI settings
_LTspeedMaximum                   = 8000000

# Radio Commands
_RADIO_GET_STATUS                 = const(0xC0)
_RADIO_WRITE_REGISTER             = const(0x18)
_RADIO_READ_REGISTER              = const(0x19)
_RADIO_WRITE_BUFFER               = const(0x1A)
_RADIO_READ_BUFFER                = const(0x1B)
_RADIO_SET_SLEEP                  = const(0x84)
_RADIO_SET_STANDBY                = const(0x80)
_RADIO_SET_TX                     = const(0x83)
_RADIO_SET_RX                     = const(0x82)
_RADIO_SET_CAD                    = const(0xC5)
_RADIO_SET_PACKETTYPE             = const(0x8A)
_RADIO_GET_PACKETTYPE             = const(0x03)
_RADIO_SET_RFFREQUENCY            = const(0x86)
_RADIO_SET_TXPARAMS               = const(0x8E)
_RADIO_SET_CADPARAMS              = const(0x88)
_RADIO_SET_BUFFERBASEADDRESS      = const(0x8F)
_RADIO_SET_MODULATIONPARAMS       = const(0x8B)
_RADIO_SET_PACKETPARAMS           = const(0x8C)
_RADIO_GET_RXBUFFERSTATUS         = const(0x17)
_RADIO_GET_PACKETSTATUS           = const(0x1D)
_RADIO_GET_RSSIINST               = const(0x1F)
_RADIO_SET_DIOIRQPARAMS           = const(0x8D)
_RADIO_GET_IRQSTATUS              = const(0x15)
_RADIO_CLR_IRQSTATUS              = const(0x97)
_RADIO_SET_REGULATORMODE          = const(0x96)
_RADIO_SET_AUTOFS                 = const(0x9E)
_RADIO_SET_RANGING_ROLE           = const(0xA3)
_PACKET_TYPE_LORA                 = const(0x01)
_PACKET_TYPE_RANGING              = const(0x02)
_PACKET_HEADER_EXPLICIT           = const(0x00) # variable length, header included
_PACKET_HEADER_IMPLICIT           = const(0x80) # fixed length, no header in packet
_PACKET_CRC_MODE_ON               = const(0x20) # 32
_PACKET_CRC_MODE_OFF              = const(0x00)
_PACKET_IQ_INVERT                 = const(0x00)
_PACKET_IQ_NORMAL                 = const(0x40) # 64
_XTAL_FREQ                        = const(52000000)
_FREQ_STEP                        = const(198.364) #= _XTAL_FREQ/262144

# Modulation Parameters Constants
# LoRa Spreading Factor
_LORA_SF5                         = const(0x50)
_LORA_SF6                         = const(0x60)
_LORA_SF7                         = const(0x70)
_LORA_SF8                         = const(0x80)
_LORA_SF9                         = const(0x90)
_LORA_SF10                        = const(0xA0)
_LORA_SF11                        = const(0xB0)
_LORA_SF12                        = const(0xC0)

# LoRa modParam2
_LORA_BW_0400                     = const(0x26) # actually 406250hz
_LORA_CR_4_5                      = const(0x01)

# SX1280 Standby modes
_MODE_STDBY_RC                    = const(0x00)
_MODE_STDBY_XOSC                  = const(0x01)

# TX and RX timeout based periods
_PERIODBASE_15_US                 = const(0x00)
_PERIODBASE_62_US                 = const(0x01)
_PERIODBASE_01_MS                 = const(0x02)
_PERIODBASE_04_MS                 = const(0x03)

# TX and RX timeouts
_TIMEOUT_0_S                      = [0x00, 0x00]
_TIMEOUT_60_S                     = [0xEA, 0x60]
_TIMEOUT_CONTINUOUS               = [0xFF, 0xFF]

# SX1280 Power settings
_USE_LDO                          = const(0x00)
_USE_DCDC                         = const(0x01)

# SX1280 Interrupt flags
_IRQ_RADIO_ALL                    = [0xFF, 0xFF]

# Radio Head Constants
_RH_BROADCAST_ADDRESS   = const(0xFF)
_RH_FLAGS_ACK           = const(0x80)
_RH_FLAGS_RETRY         = const(0x40)

# Other constants
_RXBUFFER_OFFSET                  = const(3)

_irq1Def=('RangingSlaveRequestDiscard','RangingMasterResultValid','RangingMasterTimeout','RangingMasterRequestValid','CadDone','CadDetected','RxTxTimeout','PreambleDetected')
_irq2Def=('TxDone','RxDone','SyncWordValid','SyncWordError','HeaderValid','HeaderError','CrcError','RangingSlaveResponseDone')
# _ranging_calibrations={#  SF5          SF6          SF7         SF8            SF9          SF10
#             'BW400' :[const(10299),const(10271),const(10244),const(10242),const(10230),const(10246)],
#             'BW800' :[const(11486),const(11474),const(11453),const(11426),const(11417),const(11401)],
#             'BW1600':[const(13308),const(13493),const(13528),const(13515),const(13430),const(13376)]}
# range_Freqoff={ #       SF5    SF6    SF7    SF8    SF9   SF10
#             'BW400' :[-0.148,-0.214,-0.419,-0.853,-1.686,-3.423],
#             'BW800' :[-0.041,-0.811,-0.218,-0.429,-0.853,-1.737],
#             'BW1600':[0.103, -0.041,-0.101,-0.211,-0.424,-0.87 ]}
_mode_mask = const(0xE0)
_cmd_stat_mask = const(0x1C)

class SX1280:
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

    _BUFFER = bytearray(255)

    _packetParamsLoRa = {
            'PreambleLength': 12,
            'HeaderType'    : _PACKET_HEADER_EXPLICIT,
            'PayloadLength' : 11,
            'CrcMode'       : _PACKET_CRC_MODE_ON,
            'InvertIQ'      : _PACKET_IQ_NORMAL }

    _rangingParams = {
            'SF': 0xA0,
            'BW': 0x0A,
            'CR': 0x01 }

    def __init__(self, spi, cs, reset, busy, dio2, frequency, *, preamble_length=12, baudrate=_LTspeedMaximum, debug=True, txen=False, rxen=False):
        self._device = spidev.SPIDevice(spi, cs, baudrate=baudrate, polarity=0, phase=0)
        self._dio2 = dio2
        self._reset = reset
        self._reset.switch_to_input(pull=digitalio.Pull.UP)
        self._busy = busy
        self._busy.switch_to_input()
        self._packetType = 0 # default LoRa
        self._debug = debug
        self.default_dio = dio2
        self.txen=txen
        self.rxen=rxen
        self._frequency=frequency
        self.ranging_calibration=False
        self.rng_rssi=0


        self.reset()
        self._busywait()
        self.retry_counter=0
        self.timeouts=0

        # Radio Head (RH) Stuff
        self.ack_delay = None
        self.ack_retries = 5
        self.ack_wait = 0.2
        self.sequence_number = 0
        # self.seen_ids = bytearray(256)

        # RH Header Bytes
        self.node = _RH_BROADCAST_ADDRESS
        self.destination = _RH_BROADCAST_ADDRESS
        self.identifier = 0
        self.flags = 0

        # default register configuration
        self.default_config()

    def default_config(self):
        self._sleeping=False
        self._setRanging = False
        self._ranging=False
        self._status = 0
        self._autoFS=False
        self._listen=False
        self._rangeListening=False
        self.setStandby(_MODE_STDBY_RC)
        self.setRegulatorMode(_USE_LDO)
        self.setPacketType(_PACKET_TYPE_LORA)
        self.frequencyGhz=self._frequency
        self.setBufferBaseAddress(rxBaseAddress=0x80)
        self.setModulationParams()
        self.setPacketParams()
        # self.setTxParams() # power=13dBm,rampTime=20us
        self.setDioIrqParams()
        self.setHighSensitivityLna(False) # changed to shut off May 6
        self.clearIrqStatus()

        # Set Ranging Filter Size to 200 samples
        # self._writeRegister(0x9,0x1E,20)
        # Disable Advanced Ranging
        self._sendCommand(bytes([0x9A,0]))
        # Disable long preamble
        # self._sendCommand(bytes([0x9B,0]))
        # Set Save Context
        self._sendCommand(bytes([0xD5]))

        if self._debug: print('Radio Initialized') 

    def _convertStatus(self,status):
        mode = (status & _mode_mask)>>5
        cmdstat = (status & _cmd_stat_mask)>>2
        if mode in self._status_mode:
            self._status_msg['mode']=self._status_mode[mode]
        if cmdstat in self._status_cmd:
            self._status_msg['cmd']=self._status_cmd[cmdstat]
        self._status_msg['busy'] = not bool(status & 0x1)
        return self._status_msg

    def _sendCommand(self,command,stat=True):
        if self._debug:
            print('_sendCommand()')
        _size=len(command)
        self._busywait()
        with self._device as spi:
            spi.write_readinto(command,self._BUFFER, out_end=_size,in_end=_size)
        if stat:
            print('\tcommand:',[hex(i) for i in command])
            # print('SendCMD BUF:',[hex(i) for i in self._BUFFER[:_size]])
        if self._debug:
            print('\tstatus:', '{}'.format(self._convertStatus(self._BUFFER[0])))
        
        self._busywait()
        return self._BUFFER[:_size]

    def _writeRegister(self,address1,address2,data):
        if self._debug:
            print('Writing to:',hex(address1),hex(address2))
        self._sendCommand(bytes([_RADIO_WRITE_REGISTER, address1, address2, data]))

    def _readRegister(self,address1,address2):
        if self._debug:
            print('Reading:',hex(address1),hex(address2))
        self._busywait()
        with self._device as spi:
            spi.write(bytes([_RADIO_READ_REGISTER,address1,address2]), end=3)
            spi.readinto(self._BUFFER, end=2)
        if self._debug:
            [print(hex(i),' ',end='')for i in self._BUFFER]
            print('')
        self._busywait()
        return self._BUFFER[1] # TODO this seems wrong

    def _readRegisters(self,address1,address2,_length=1):
        '''
        read_reg_cmd,   addr[15:8],     addr[7:0],   NOP,    NOP,    NOP,    NOP,  ...
            status        status         status     status  data1   data2   data3  ...
        '''
        _size = _length + 4
        if self._debug: print('Reading:',hex(address1),hex(address2))
        self._busywait()
        with self._device as spi:
            spi.write_readinto(bytes([_RADIO_READ_REGISTER,address1,address2,0]+[0]*_length),self._BUFFER,out_end=_size,in_end=_size)
        self._busywait()
        if self._debug: print('Read Regs ({}, {}) _BUFFER: {}'.format(hex(address1),hex(address2),[hex(i) for i in self._BUFFER]))
        return self._BUFFER[4:_size]

    def printRegisters(self,start=0x0900,stop=0x09FF,p=True):
        _length=stop-start+1
        _size=_length+4
        buff=bytearray(_size)
        self._busywait()
        with self._device as spi:
            spi.write_readinto(bytes([_RADIO_READ_REGISTER])+int(start).to_bytes(2,'big')+b'\x00'+b'\x00'*_length,buff,out_end=_size,in_end=_size)
        if p:
            pass
        else:
            return buff

    # @timeout(3)
    def _busywait(self):
        _t = monotonic() + 3
        while monotonic() < _t:
            # if self._debug: print('waiting for busy pin.')
            if not self._busy.value:
                return True
        print('TIMEOUT on busywait')
        self.timeouts+=1
        if self.timeouts > 5:
            self.timeouts=0
            try:
                with open('/sd/log.txt','a') as f:
                    f.write('sb:{}\n'.format(int(monotonic())))
            except: pass
            self.reset_io()
        if hasattr(self,'timeout_handler'): self.timeout_handler()
        return False

    def reset_io(self):
        self._reset.switch_to_output(value=False)
        self._busy.switch_to_input()
        sleep(5)
        self._reset.switch_to_input(pull=digitalio.Pull.UP)
        sleep(2)
        self.default_config()

    def wait_for_irq(self):
        if self.default_dio:
            return self.DIOwait(self.default_dio)
        else:
            return self.IRQwait(bit=1)

    # @timeout(3)
    def DIOwait(self,pin):
        _t=monotonic()+3
        while monotonic()<_t:
            if pin.value:
                self.clearIrqStatus()
                return True
        print('TIMEDOUT on DIOwait')
        if hasattr(self,'timeout_handler'): self.timeout_handler()
        return False

    # @timeout(4)
    def IRQwait(self,bit):
        _t=monotonic()+4
        while monotonic()<_t:
            _irq=self.getIrqStatus(clear=False)[1] & 1
            # print(hex(_irq))
            if (_irq >> bit) & 1:
                return True
        print('TIMEDOUT on IRQwait')
        if hasattr(self,'timeout_handler'): self.timeout_handler()
        return False

    def setRegulatorMode(self,mode=_USE_LDO): # changed default mode to LDO
        if self._debug:
            print('Setting Regulator Mode')
        self._sendCommand(bytes([_RADIO_SET_REGULATORMODE, mode]))

    def reset(self):
        self._reset.switch_to_output(value=False)
        sleep(0.05)  # 50 ms
        self._reset.switch_to_input(pull=digitalio.Pull.UP)
        sleep(0.03)  # 30 ms

    def setStandby(self, state=_MODE_STDBY_RC):
        if self._debug: print('Setting Standby')
        self._sendCommand(bytes([_RADIO_SET_STANDBY, state]))

    def sleep(self):
        self._busywait()
        with self._device as spi:
            spi.write_readinto(bytes([_RADIO_SET_SLEEP, 0x07]),self._BUFFER,out_end=2,in_end=2)
        self._sleeping=True
        if self._debug:
            print('\t\tSleeping SX1280')
            print('\t\t{}'.format(self._convertStatus(self._BUFFER[0])))

    def wakeUp(self):
        if self._sleeping:
            if self._debug: print('\t\tWaking SX1280')
            with self._device as spi:
                sleep(0.1)
                spi.write(bytes([0xC0,0])) # send no-op to wake-up
            if not self._busywait():
                print('wakeUp busy fail')
            # reinitalize
            self.default_config()

    def setPacketType(self,packetType=_PACKET_TYPE_LORA):
        if self._debug:
            print('Setting Packet Type')
        self._sendCommand(bytes([_RADIO_SET_PACKETTYPE, packetType]))
        self._packetType = packetType

    def setCadParams(self,symbol=0x80):
        if self._debug: print('Setting CAD Parameters')
        self._sendCommand(bytes([_RADIO_SET_CADPARAMS, symbol]))

    def set_Cad(self):
        if self._debug: print('Setting CAD Search')
        self._sendCommand(bytes([_RADIO_SET_CAD]))
        self.clearIrqStatus()

    @property
    def frequencyGhz(self):
        return float(str(self._frequency)+"E"+"9")

    @frequencyGhz.setter
    def frequencyGhz(self,freq):
        '''
        0xB89D89 = 12098953 PLL steps = 2.4 GHz
        2.4 GHz  = 12098953*(52000000/(2**18))
        '''
        self._frequency=freq
        _f=int(float(str(freq)+"E"+"9")/_FREQ_STEP)
        if self._debug: print('\tSX1280 freq: {:G} GHz ({} PLL steps)'.format(float(str(freq)),_f))
        
        freq_buffer = []
        freq_buffer.append( (_f >> 16) & 0xFF )
        freq_buffer.append(( _f >> 8) & 0xFF )
        freq_buffer.append( _f & 0xFF )
        
        self._sendCommand(bytes([_RADIO_SET_RFFREQUENCY, freq_buffer[0], freq_buffer[1], freq_buffer[2]]))

    def setBufferBaseAddress(self,txBaseAddress=0x00,rxBaseAddress=0x00):
        if self._debug: print('Setting Buffer Base Address')
        self._txBaseAddress = txBaseAddress
        self._rxBaseAddress = rxBaseAddress
        self._sendCommand(bytes([_RADIO_SET_BUFFERBASEADDRESS, txBaseAddress, rxBaseAddress]))

    def setModulationParams(self, modParam1=_LORA_SF7, modParam2=_LORA_BW_0400, modParam3=_LORA_CR_4_5):
        # LoRa with SF7, (BW1600=0x0A -> changed to BW400=0x26), CR 4/5
        # Must set PacketType first! - See Table 13-48,49,50
        if self._debug: print('Setting Modulation parameters')
        self._sendCommand(bytes([_RADIO_SET_MODULATIONPARAMS, modParam1, modParam2, modParam3]))
        
        # implement data sheet additions, datasheet SX1280-1_V3.2section 14.47
        if self._packetType == _PACKET_TYPE_LORA:
            self._busywait()

            if (modParam1 == _LORA_SF5) or (modParam1 == _LORA_SF6):
                self._writeRegister(0x09, 0x25, 0x1E)

            elif (modParam1 == _LORA_SF7) or (modParam1 == _LORA_SF8):
                self._writeRegister(0x09, 0x25, 0x37)

            elif ( (modParam1 == _LORA_SF9) or (modParam1 == _LORA_SF10) or 
                (modParam1 == _LORA_SF11) or (modParam1 == _LORA_SF12) ):
                self._writeRegister(0x09, 0x25, 0x32)

            else:
                print('Invalid Spreading Factor')

    def setPacketParams(self):
        if self._debug: print(self._packetParamsLoRa)
        self._sendCommand(
            bytes([
                _RADIO_SET_PACKETPARAMS,
                self._packetParamsLoRa['PreambleLength'],
                self._packetParamsLoRa['HeaderType'],
                self._packetParamsLoRa['PayloadLength'],
                self._packetParamsLoRa['CrcMode' ],
                self._packetParamsLoRa['InvertIQ'],
                0x00,
                0x00
            ]))

    def setTxParams(self,power=0x1C,rampTime=0x00):
        # power=10 dBm (0x1C), rampTime=2us (0x00). See Table 11-47
        # P=-18+power -18+0x1C=10
        if self._debug:
            print('Setting Tx Parameters')
        self._sendCommand(bytes([_RADIO_SET_TXPARAMS,power,rampTime]))

    def writeBuffer(self,data):
        #Offset will correspond to txBaseAddress in normal operation.
        _offset = self._txBaseAddress
        _len = len(data)
        assert 0 < _len <= 252
        self._busywait()
        with self._device as spi:
            spi.write(bytes([_RADIO_WRITE_BUFFER,_offset])+data,end=_len+2)

    def readBuffer(self,offset,payloadLen):
        if self._debug:
            print("readBuffer()")
            print("\tpayloadLen: ", payloadLen)
        _payload = bytearray(payloadLen)
        
        # Make sure the radio is not busy
        self._busywait()

        zeros = [0x00 for i in range(payloadLen)]

        self._sendCommand(bytes([_RADIO_READ_BUFFER, offset] + zeros))
        rxBuffer = self._BUFFER[_RXBUFFER_OFFSET : _RXBUFFER_OFFSET + (payloadLen-1)]

        return rxBuffer

    def dump_buffer(self,dbuffer):
        self._busywait()
        with self._device as spi:
            spi.write(bytes([_RADIO_READ_BUFFER,0,0]), end=3)
            spi.readinto(dbuffer)
        # print('Status:',self._convertStatus(self._BIGBUFFER[0]))
        # [print(hex(i),end=',') for i in self._BIGBUFFER[1:]]
        # print('')

    def get_bw(self,_bw):
        if _bw==0x0A:
            bw_hz=1625000
        elif _bw==0x18:
            bw_hz= 812500
        elif _bw==0x26:
            bw_hz= 406250
        elif _bw==0x34:
            bw_hz= 203125
        else:
            print('bad BW conversion')
            return 0
        return bw_hz


    def setDioIrqParams(self,irqMask=[0xFF,0xFF],dio1Mask=[0x00,0x00],dio2Mask=[0x44, 0x6B],dio3Mask=[0x00,0x00]):
        '''
        Enable all interrupts and set TxDone, RxDone, and Errors to DIO2.
        0100 0100 0110 1011
        [0x44, 0x6B]
        '''
        if self._debug: print('Setting DIO IRQ Parameters')
        self._sendCommand(bytes([_RADIO_SET_DIOIRQPARAMS]+irqMask+dio1Mask+dio2Mask+dio3Mask))

    def clearIrqStatus(self, irqMask=_IRQ_RADIO_ALL):
        if self._debug: print('Clearing IRQ Status')
        self._sendCommand(bytes([_RADIO_CLR_IRQSTATUS]+irqMask))

    def getIrqStatus(self,clear=[0xFF,0xFF],parse=True,debug=False):
        if self._debug: print('getIrqStatus()')
        _, _, _irq1,_irq2 = self._sendCommand(bytes([_RADIO_GET_IRQSTATUS,0x00,0x00,0x00]))

        if parse:
            if debug:
                print('\tIRQ[15:8]:{}, IRQ[7:0]:{}'.format(hex(_irq1),hex(_irq2))) #
            _rslt=[]
            for i,j in zip(reversed('{:08b}'.format(_irq1)),_irq1Def): # [15:8]
                if int(i):
                    _rslt.append(j)
            for i,j in zip(reversed('{:08b}'.format(_irq2)),_irq2Def): # [7:0]
                if int(i):
                    _rslt.append(j)
            if self._debug: print('\tIRQ Results: {}'.format(_rslt))
            return((_rslt,hex(_irq1),hex(_irq2)))

        if clear:
            if clear==True:
                clear=[0xFF,0xFF]
            self._sendCommand(bytes([_RADIO_CLR_IRQSTATUS]+clear)) # clear IRQ status
        return (_irq1,_irq2)

    def setTx(self, timeoutTx=_TIMEOUT_0_S):
        #Activate transmit mode with no timeout. Tx mode will stop after first packet sent.
        if self._debug: print('Setting Tx')
        # self.clearIrqStatus([8,7])
        self.clearIrqStatus()
        self._sendCommand(bytes([_RADIO_SET_TX, _PERIODBASE_01_MS] + timeoutTx))
        self._listen=False

    def setRx(self, timeoutRx=_TIMEOUT_60_S):
        '''
        timeoutRx = 16 bit parameter of how many steps to time-out
        see Table 11-22 for pBase values (0xFFFF=continuous, 0xEA60=60s timeout, or 60000ms)
        Time-out duration = pBase * periodBaseCount
        '''
        if self._debug: print('Setting Rx')

        if self.rxen:
            self.txen.value=False
            self.rxen.value=True

        self.clearIrqStatus()
        self._sendCommand(bytes([_RADIO_SET_RX, _PERIODBASE_01_MS] + timeoutRx))

    def setAutoFs(self,value):
        self._sendCommand(bytes([_RADIO_SET_AUTOFS, bool(value)]))
        self._autoFS=value

    def setHighSensitivityLna(self,enabled=True):
        _reg=self._readRegister(0x8,0x91)
        if enabled:
            self._writeRegister(0x8,0x91,_reg | 0xC0)
        else:
            self._writeRegister(0x8,0x91,_reg & 0x3F)

    def clearRangeSamples(self):
        # to clear, set bit 5 to 1 then to 0
        _reg=self._readRegister(0x9,0x23)
        # print('Register 0x923:',hex(_reg))
        _reg |= (1 << 5)
        # print('Register 0x923:',hex(_reg))
        self._writeRegister(0x9,0x23,_reg)
        _reg &= ~(1 << 5)
        # print('Register 0x923:',hex(_reg))
        self._writeRegister(0x9,0x23,_reg)

    def set_Ranging_Params(self,range_addr=[0x01,0x02,0x03,0x04], master=False, slave=False):
        self.setStandby(_MODE_STDBY_RC)
        self.clearRangeSamples()
        self.setPacketType(_PACKET_TYPE_RANGING)
        self.setModulationParams(modParam1=self._rangingParams['SF'],modParam2=self._rangingParams['BW'],modParam3=self._rangingParams['CR'])
        self._packetParamsLoRa['PreambleLength']=12
        self._packetParamsLoRa['PayloadLength']=0
        self.setPacketParams()
        self.frequencyGhz=self._frequency
        self.setBufferBaseAddress(txBaseAddress=0x00,rxBaseAddress=0x00)
        self.setTxParams() # DEFAULT:power=13dBm,rampTime=20us
        if slave:
            self._rangingRole = 0x00
            # Slave Ranging address
            self._writeRegister(0x9,0x19,range_addr[0])
            self._writeRegister(0x9,0x18,range_addr[1])
            self._writeRegister(0x9,0x17,range_addr[2])
            self._writeRegister(0x9,0x16,range_addr[3])
            # Ranging address length
            self._writeRegister(0x9,0x31,0x3)
            # self.setDioIrqParams(irqMask=[0x7F,0xF3],dio1Mask=[0x00,0x83],dio2Mask=[0x00,0x03],dio3Mask=[0x40,0x20]) # wrong? RangingSlaveResponseDone,RxDone,TxDone
            # self.setDioIrqParams(irqMask=[0x7F,0xF3],dio1Mask=[0x9,0x80],dio2Mask=[0x00,0x03],dio3Mask=[0x40,0x20]) # RangingMasterRequestValid,RangingSlaveRequestDiscard,RangingSlaveResponseDone
            self.setDioIrqParams(irqMask=[0x7F,0xF3],dio1Mask=[0x1,0x80],dio2Mask=[0x00,0x03],dio3Mask=[0x40,0x20]) # RangingSlaveRequestDiscard,RangingSlaveResponseDone
        elif master:
            self._rangingRole = 0x01
            # Master Ranging address
            self._writeRegister(0x9,0x15,range_addr[0])
            self._writeRegister(0x9,0x14,range_addr[1])
            self._writeRegister(0x9,0x13,range_addr[2])
            self._writeRegister(0x9,0x12,range_addr[3])
            # self.setDioIrqParams(irqMask=[0x7F,0xF3],dio1Mask=[0x7,0x80],dio2Mask=[0x00,0x01],dio3Mask=[0x00,0x00]) # wrong? RangingMasterTimeout,RangingMasterResultValid,RangingSlaveRequestDiscard,RangingSlaveResponseDone
            self.setDioIrqParams(irqMask=[0x7F,0xF3],dio1Mask=[0x6,0x00],dio2Mask=[0x00,0x01],dio3Mask=[0x00,0x00]) # RangingMasterTimeout,RangingMasterResultValid

        else:
            print('Select Master or Slave Only')
            return False

        # Set DIO IRQ Parameters
        self.clearIrqStatus()

        if self.ranging_calibration == 'custom':
            self.set_Ranging_Calibration(custom=self.rxtxdelay)
        elif self.ranging_calibration:
            self.set_Ranging_Calibration(zero=True)
        else:
            # Set Ranging Calibration per Section 3.3 of SemTech AN1200.29
            # TODO set based on modulation params
            # self.set_Ranging_Calibration(CAL='BW1600',SF=5)
            # self.set_Ranging_Calibration(CAL='BW1600',SF=9)
            self.set_Ranging_Calibration(CAL='BW1600',SF=10)

        # Set Ranging Role
        self._sendCommand(bytes([_RADIO_SET_RANGING_ROLE, self._rangingRole]))

        self.setHighSensitivityLna(True)

        self._setRanging = True

    def stop_ranging(self):
        self.setStandby(_MODE_STDBY_RC)
        self.setPacketType(_PACKET_TYPE_LORA)
        self.setPacketParams()
        self.setHighSensitivityLna(True)
        self.setDioIrqParams()
        if self.txen:
            self.txen.value=False
            self.rxen.value=False
        self._setRanging = False

    def read_range(self,raw=True,raw_bytes=False):
        if not self._ranging:
            print('Start ranging before attempting to read')
            return

        self.setStandby(_MODE_STDBY_XOSC)
        #enable LoRa modem clock
        _temp=self._readRegister(0x9,0x7F) | (1 << 1)
        self._writeRegister(0x9,0x7F,_temp)
        # Set the ranging type for filtered or raw
        _conf=self._readRegister(0x9,0x24)
        if raw:
            _conf = (_conf & 0xCF) | 0x0
        else:
            # _conf = (_conf & 0xCF) | 0x10 # averaged
            # _conf = (_conf & 0xCF) | 0x20 # debiased
            _conf = (_conf & 0xCF) | 0x30 # filtered
        # print('Range Data Type:',hex(_conf))
        self._writeRegister(0x9,0x24,_conf)

        # Read the 24-bit value
        self._rbuff=bytearray(4)
        self._rbuff=self._readRegisters(0x9,0x61,4) # confirmed working
        self.rng_rssi=-1*self._rbuff[3]/2
        # print('rng_rssi: {}'.format(self.rng_rssi))

        self.setStandby(_MODE_STDBY_RC)

        if raw_bytes:
            return self._rbuff[:3]

        _val = 0 | (self._rbuff[0] << 16)
        _val |= (self._rbuff[1] << 8)
        _val |= (self._rbuff[2])

        # dist in meters = _val * 150/(2^12 * BW in MHz) = 2scomp / (BW in Hz * 36621.09375)
        _2scomp = self.complement2(_val,24) / self.get_bw(self._rangingParams['BW']) * 36621.09375
        if raw: return _2scomp
        # averaged, debiased, or filtered results
        return _2scomp * 20.0 / 100.0

    def get_Freq_Error_Indicator(self):
        # Read the 20-bit value (based on StuartsProjects github implementation)
        self.setStandby(_MODE_STDBY_XOSC)
        efeRaw=self._readRegisters(0x9,0x54,3)
        efeRaw[0]=efeRaw[0]&0x0F #clear bit 20 which is always set
        self.setStandby(_MODE_STDBY_RC)
        return efeRaw

    def set_Ranging_Calibration(self,CAL='BW1600',SF=5,zero=False,custom=False):
        if zero:
            CAL=0
        elif custom:
            CAL=custom
        else:
            CAL=0
        self._writeRegister(0x9,0x2D,CAL&0xFF)      # cal[7:0]
        self._writeRegister(0x9,0x2C,(CAL>>8)&0xFF) # cal[15:8]

    def calc_efe(self,efeRaw):
        efe = 0 | (efeRaw[0]<< 16)
        efe |= (efeRaw[1]<< 8)
        efe |= (efeRaw[2])
        # efe &= 0x0FFFFF # now performed in get_Freq_Error_Indicator step
        efeHz = 1.55 * self.complement2(efe,20) / (1625000/self.get_bw(self._rangingParams['BW']))
        return efeHz

    def complement2(self,num,bitCnt):
        retVal = num
        if retVal >= 2<<(bitCnt-2):
            retVal -= 2<<(bitCnt-1)
        return retVal

    def getPacketStatus(self):
        # See Table 11-63
        # self._packet_status = []
        packetStatus = self._sendCommand(bytes([_RADIO_GET_PACKETSTATUS,0x00,0x00,0x00,0x00,0x00,0x00]))
        # [print(hex(i)+' ',end='') for i in self._BUFFER[:6]]
        self.rssiSync = int(-1*(packetStatus[2])/2)
        self.snr = int((packetStatus[3])/4)
        return packetStatus

    def getRxBufferStatus(self):
        _, _, rxPayloadLength, rxStartBufferPointer = self._sendCommand(bytes([_RADIO_GET_RXBUFFERSTATUS,0x00,0x00,0x00]))
        return [rxPayloadLength, rxStartBufferPointer]

    def send(self, data, pin=None,irq=False,header=True,ID=0,target=0,action=0,keep_listening=False):
        """Send a string of data using the transmitter.
           You can only send 252 bytes at a time
           (limited by chip's FIFO size and appended headers).
        """
        return self.send_mod(data,keep_listening=keep_listening,header=header)


    @property
    def packet_status(self):
        self.getPacketStatus()
        return (self.rssiSync,self.snr)

    @property
    def listen(self):
        return self._listen

    @listen.setter
    def listen(self, enable):
        if enable:
            if not self._listen:
                if self.rxen:
                    self.txen.value=False
                    self.rxen.value=True
                self.setRx()
                self._listen = True
        else:
            if self.rxen:
                self.rxen.value=False
            self.setStandby(_MODE_STDBY_RC)
            self._listen = False

    def receive(self, keep_listening=True, timeout=15, debug=True):
        if not self.default_dio:
            print('must set default DIO!')
            return False

        # self.listen = True # call setRx()
        self.setRx()

        timed_out = False
        start = monotonic()

        # Blocking wait for interrupt on DIO
        while not timed_out and not self.default_dio.value:
            if (monotonic() - start) >= timeout:
                timed_out = True

        # Radio has received something!
        # packet = None
        # received a packet, so stop listening
        # self.listen = False

        self.setStandby(_MODE_STDBY_RC)
        if not timed_out:

            regdata = self.getIrqStatus()

            self._rxBufferStatus = self.getRxBufferStatus()
            self._packetLength = self._rxBufferStatus[0]
            self._packetPointer = self._rxBufferStatus[1]

            if self._packetLength > 0:
                if self._debug:
                    print('Offset:',self._packetPointer,'Length:',self._packetLength)
                packet = self.readBuffer(offset=self._packetPointer,payloadLen=self._packetLength+1) # +1 to account for the extra byte sent back
                
                regdata = self.getIrqStatus()

                # if not keep_listening:
                #     self.listen = False
                return packet

    @property
    def packet_info(self):
        return (self._packetLength,self._packetPointer)

    def rssi(self,raw=False):
        self._rssi = self._sendCommand(bytes([_RADIO_GET_PACKETSTATUS,0x00,0x00]))
        if raw:
            return self._rssi[-1]
        else:
            return -1*self._rssi[-1]/2 # dBm

    def status(self, raw=False):
        self._busywait()
        with self._device as spi:
            spi.write_readinto(bytes([_RADIO_GET_STATUS]),self._BUFFER,out_end=1,in_end=1)
        # if raw: print([hex(i) for i in self._BUFFER])
        if raw:
            return self._BUFFER[0]
        self._busywait()
        return self._convertStatus(self._BUFFER[0])

    def send_mod(
        self,
        data,
        *,
        keep_listening=False,
        header=False,
        destination=None,
        node=None,
        identifier=None,
        flags=None,
        debug=False):
        data_len = len(data)
        assert 0 < data_len <= 252
        if self.txen:
            self.rxen.value=False
            self.txen.value=True
            if debug: print('\t\ttxen:on, rxen:off')
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
            if debug: print('HEADER: {}'.format([hex(i) for i in payload]))
            data = payload + data
            data_len+=4
        # Configure Packet Length
        self._packetParamsLoRa['PayloadLength']=data_len
        self.setPacketParams()
        self.writeBuffer(data)
        self.setTx()
        txdone=self.wait_for_irq()
        if keep_listening:
            self.listen=True
        else:
            if self.txen:
                self.txen.value=False
                if debug: print('\t\ttxen:off, rxen:n/a')
        return txdone

    def receive_mod(
        self, *, keep_listening=True, with_header=False, with_ack=False, timeout=15,debug=True):
        timed_out = False
        if not self.default_dio:
            print('must set default DIO!')
            return False
        if timeout is not None:
            # if not self._listen:
            self.listen = True
            start = monotonic()
            timed_out = False
            # Blocking wait for interrupt on DIO
            while not timed_out and not self.default_dio.value:
                if (monotonic() - start) >= timeout:
                    timed_out = True
        # Radio has received something!
        packet = None
        # Stop receiving other packets
        self.listen=False
        if not timed_out:

            regdata = self.getIrqStatus()

            # print('IRQ status registers:', bin(regdata), bin(reg_lower))

            # if (regdata & IRQ_HEADER_ERROR) | (regdata & IRQ_CRC_ERROR) | (regdata & IRQ_RX_TX_TIMEOUT ) | (regdata & IRQ_SYNCWORD_ERROR ): #check if any of the preceding IRQs is set
            #     return 0 # packet is errored somewhere so return 0

            self._rxBufferStatus = self.getRxBufferStatus()
            self._packetLength = self._rxBufferStatus[0]
            self._packetPointer = self._rxBufferStatus[1]
            if self._debug:
                print('Offset:',self._packetPointer,'Length:',self._packetLength)
            if self._packetLength > 0:
                packet = self.readBuffer(offset=self._packetPointer,payloadLen=self._packetLength+1)[1:]
            self.clearIrqStatus()
            if self._packetLength > 4:
                if (self.node != _RH_BROADCAST_ADDRESS
                    and packet[0] != _RH_BROADCAST_ADDRESS
                    and packet[0] != self.node):
                    if debug: print('Overheard packet:',packet)
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
                    # print('sband ack to {}'.format(packet[1]))
                # if not with_header:  # skip the header if not wanted
                #     packet = packet[4:]
        # Listen again if necessary and return the result packet.
        if keep_listening:
            self.listen=True
        return packet

    def send_with_ack(self, data):
        """Reliable Datagram mode:
           Send a packet with data and wait for an ACK response.
           The packet header is automatically generated.
           If enabled, the packet transmission will be retried on failure
        """
        if self.ack_retries:
            retries_remaining = self.ack_retries
        else:
            retries_remaining = 1
        got_ack = False
        self.retry_counter=0
        self.sequence_number = (self.sequence_number + 1) & 0xFF
        while not got_ack and retries_remaining:
            self.identifier = self.sequence_number
            self.send_mod(data, header=True, keep_listening=True)
            # Don't look for ACK from Broadcast message
            if self.destination == _RH_BROADCAST_ADDRESS:
                print('sband destination=RHbroadcast address (dont look for ack)')
                got_ack = True
            else:
                # wait for a packet from our destination
                ack_packet = self.receive_mod(timeout=self.ack_wait, with_header=True)
                if ack_packet is not None:
                    if ack_packet[3] & _RH_FLAGS_ACK:
                        # check the ID
                        if ack_packet[2] == self.identifier:
                            got_ack = True
                            break
                        else:
                            print('bad sband ack ID. Looking for: {}'.format(hex(self.identifier)))
            # delay random amount before retry
            if not got_ack:
                self.retry_counter+=1
                print('no sband ack, sending again...')
                sleep(self.ack_wait + self.ack_wait * random())
            retries_remaining = retries_remaining - 1
            # set retry flag in packet header
            self.flags |= _RH_FLAGS_RETRY
        self.flags = 0  # clear flags
        return got_ack

    def get_range(self,addr=[0,0,0,0],raw=False,timeout=10,t_resend=3,debug=False,delay=1):
        timed_out = False
        irq=[]
        if not self.default_dio:
            print('must set default DIO!')
            return False
        # sleep a delayed amount to give slave time to configure
        sleep(delay)
        self.set_Ranging_Params(range_addr=addr,master=True)
        self.setTx(timeoutTx=_TIMEOUT_CONTINUOUS) # reduced pbase to 1ms

        if timeout is not None:
            resend = monotonic()+t_resend
            timed_out = monotonic()+timeout
            while monotonic() < timed_out:
                if self.default_dio.value:
                    irq=self.getIrqStatus(clear=True,parse=True)[0]
                    if irq:
                        # print('m',irq)
                        if debug: print(irq)
                        if 'RngMasterResultValid' in irq:
                            self._ranging=True
                            self.clearIrqStatus()
                            return self.read_range(raw_bytes=raw)
                        elif 'RngMasterTimeout' in irq:
                            print('\t\t[master] RngMasterTimeout. Resending...')
                            sleep(0.5)
                            self.set_Ranging_Params(range_addr=addr,master=True)
                            self.setTx(timeoutTx=_TIMEOUT_CONTINUOUS)
                if monotonic() > resend:
                    self.set_Ranging_Params(range_addr=addr,master=True)
                    self.setTx(timeoutTx=_TIMEOUT_CONTINUOUS)
                    print('\t\t[master] resend timout')
                    resend=monotonic()+t_resend
            print('\t\t[master] timed out')
            self.getIrqStatus(clear=[0xFF,0xFF],parse=False)[0]
            self.setStandby(_MODE_STDBY_RC)
            return None

    def receive_range(self,addr=[0,0,0,0],timeout=5,t_resend=3,debug=False):
        timed_out = False
        if not self.default_dio:
            print('must set default DIO!')
            return False
        self.set_Ranging_Params(range_addr=addr,slave=True)
        self.setRx(timeoutRx=_TIMEOUT_CONTINUOUS) # reduced pbase to 1ms

        if timeout is not None:
            resend = monotonic()+t_resend
            timed_out = monotonic()+timeout
            # Blocking wait for interrupt on DIO
            while monotonic() < timed_out:
                if self.default_dio.value:
                    irq=self.getIrqStatus(clear=True,parse=True)[0]
                    if irq:
                        # print('s',irq)
                        if debug: print(irq)
                        if 'RngSlaveResponseDone' in irq:
                            self._ranging=True
                            self.setStandby(_MODE_STDBY_RC)
                            self.clearIrqStatus()
                            if debug: print('[range slave] responded to range request')
                            return True
                        elif 'RngSlaveReqDiscard' in irq:
                            print('\t\t[slave] RngSlaveReqDiscard. Listening again')
                            self.set_Ranging_Params(range_addr=addr,slave=True)
                            self.setRx(timeoutRx=_TIMEOUT_CONTINUOUS)
                if monotonic() > resend:
                    self.set_Ranging_Params(range_addr=addr,slave=True)
                    self.setRx(timeoutRx=_TIMEOUT_CONTINUOUS)
                    print('\t\t[slave] receive timeout')
                    resend=monotonic()+t_resend
            print('SLAVE timed out {}'.format(monotonic()))
            irq=self.getIrqStatus(clear=[0xFF,0xFF],parse=False)
            print(irq)
            self.setStandby(_MODE_STDBY_RC)
            return False

    def send_fast(self,data,l):
        self.txen.value=True
        self._packetParamsLoRa['PayloadLength']=l
        self.setPacketParams()
        self._busywait()
        with self._device as spi:
            spi.write(b'\x1a\x00'+data,end=l+2)
        self.setTx()
        txdone=self.wait_for_irq()
        self.txen.value=False
        return txdone
