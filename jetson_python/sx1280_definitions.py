# File name: sx1280_definitions.py
#
# Date created: May 15, 2024
#
# Author: Tara Kong
#
# Description: Radio constants and definitions

from micropython import const

# SPI SETTINGS
_LTspeedMaximum                     = 8000000

# RADIO COMMANDS
_RADIO_GET_STATUS                   = const(0xC0)
_RADIO_WRITE_REGISTER               = const(0x18)
_RADIO_READ_REGISTER                = const(0x19)
_RADIO_WRITE_BUFFER                 = const(0x1A)
_RADIO_READ_BUFFER                  = const(0x1B)
_RADIO_SET_SLEEP                    = const(0x84)
_RADIO_SET_STANDBY                  = const(0x80)
_RADIO_SET_TX                       = const(0x83)
_RADIO_SET_RX                       = const(0x82)
_RADIO_SET_CAD                      = const(0xC5)
_RADIO_SET_PACKETTYPE               = const(0x8A)
_RADIO_GET_PACKETTYPE               = const(0x03)
_RADIO_SET_RFFREQUENCY              = const(0x86)
_RADIO_SET_TXPARAMS                 = const(0x8E)
_RADIO_SET_CADPARAMS                = const(0x88)
_RADIO_SET_BUFFERBASEADDRESS        = const(0x00)#= const(0x8F)
RADIO_SET_MODULATIONPARAMS         = const(0x8B)
RADIO_SET_PACKETPARAMS             = const(0x8C)
_RADIO_GET_RXBUFFERSTATUS           = const(0x17)
_RADIO_GET_PACKETSTATUS             = const(0x1D)
_RADIO_GET_RSSIINST                 = const(0x1F)
_RADIO_SET_DIOIRQPARAMS             = const(0x8D)
_RADIO_GET_IRQSTATUS                = const(0x15)
_RADIO_CLR_IRQSTATUS                = const(0x97)
_RADIO_SET_REGULATORMODE            = const(0x96)
_RADIO_SET_RANGING_ROLE             = const(0xA3)

RADIO_SET_AUTOFS                   = const(0x9E)       # Enable or disable Auto FS Mode
RADIO_SET_FS                       = const(0xC1)       # Set the device in Frequency Synthesizer Mode

PACKET_TYPE_LORA                    = const(0x01)
_PACKET_TYPE_RANGING                = const(0x02)
_PACKET_HEADER_EXPLICIT             = const(0x00)       # variable length, header included
_PACKET_HEADER_IMPLICIT             = const(0x80)       # fixed length, no header in packet
_PACKET_CRC_MODE_ON                 = const(0x20)       # 32
_PACKET_CRC_MODE_OFF                = const(0x00)
_PACKET_IQ_INVERT                   = const(0x00)
_PACKET_IQ_NORMAL                   = const(0x40)       # 64
_XTAL_FREQ                          = const(52000000)
_FREQ_STEP                          = const(198.364)    #= _XTAL_FREQ/262144


# MODULATION PARAMETERS
LORA_SF7                           = const(0x70)   # LoRa modparam1: Spreading Factor
LORA_BW_0400                       = const(0x26)   # LoRa modParam2: Bandwidth (actually 406250hz)
LORA_CR_4_5                        = const(0x01)   # LoRa modParam3: Coding rate

# SX1280 Standby modes
MODE_STDBY_RC                      = const(0x00)
MODE_STDBY_XOSC                    = const(0x01)

# TX and RX timeout based periods
_PERIODBASE_15_US                   = const(0x00)
_PERIODBASE_62_US                   = const(0x01)
_PERIODBASE_01_MS                   = const(0x02)
_PERIODBASE_04_MS                   = const(0x03)

# TX and RX timeouts
_TIMEOUT_0_S                        = [0x00, 0x00]
_TIMEOUT_60_S                       = [0xEA, 0x60]
_TIMEOUT_CONTINUOUS                 = [0xFF, 0xFF]

# SX1280 Power settings
USE_LDO                            = const(0x00)
USE_DCDC                           = const(0x01)

# SX1280 Interrupt flags
IRQ_RADIO_ALL                      = [0xFF, 0xFF]

# Radio Head Constants
# TODO: probably don't need these
_RH_BROADCAST_ADDRESS               = const(0xFF)
_RH_FLAGS_ACK                       = const(0x80)
_RH_FLAGS_RETRY                     = const(0x40)

# Other constants
_RXBUFFER_OFFSET                    = const(3)

# CONFIGURING FLRC
PREAMBLE_LENGTH_16_BITS            = const(0x30)
FLRC_SYNC_WORD_LEN_P32S            = const(0x04)   # FLRC sync word length 4 bytes
RADIO_RX_MATCH_SYNCWORD_1          = const(0x10)
RADIO_PACKET_VARIABLE_LENGTH       = const(0x20)
PACKET_TYPE_FLRC                   = const(0x03)
RADIO_WHITENING_OFF                = const(0x08)
RADIO_RAMP_04_US                   = const(0x20)
RXBUFFER_SIZE                      = const(0x7F)   # 127 bytes length payload
RETAIN_None                        = const(0x00)   # Sleep mode
FLRC_BR_1_300_BW_1_2               = const(0x45)   # FLRC modparam1: bandwidth and bit rate, 1.3Mbs
FLRC_CR_1_0                        = const(0x04)   # FLRC modparam2: coding rate
RADIO_MOD_SHAPING_BT_1_0           = const(0x10)   # FLRC modparam3: BT
RADIO_CRC_OFF                      = const(0x00)

# REGISTERS
REG_LR_FLRCPAYLOADLENGTH           = [0x09, 0xC3]
REG_FLRCSYNCWORD1_BASEADDR         = const(0x09CF)
