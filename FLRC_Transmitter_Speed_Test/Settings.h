/*******************************************************************************************************
  Programs for Arduino - Copyright of the author Stuart Robinson - 29/09/21

  This program is supplied as is, it is up to the user of the program to decide if the program is
  suitable for the intended purpose and free from errors.
*******************************************************************************************************/

//*******  Setup hardware pin definitions here ! ***************

//These are the pin definitions for one of my own boards, the Easy Pro Mini,
//be sure to change the definitions to match your own setup.

#define NSS 5
#define SCK 18
#define MISO 19
#define MOSI 23

#define RFBUSY 25
#define NRESET 27

#define LED1 2
#define DIO1 35
#define DIO2 34
#define RX_EN -1                //pin for RX enable, used on some SX1280 devices, set to -1 if not used
#define TX_EN -1                //pin for TX enable, used on some SX1280 devices, set to -1 if not used                        

#define LORA_DEVICE DEVICE_SX1280                         //we need to define the device we are using  

//FLRC Modem Parameters
const uint32_t Frequency = 2420000000UL;                    //frequency of transmissions
const int32_t Offset = 0;                                 //offset frequency for calibration purposes

const uint8_t BandwidthBitRate = FLRC_BR_1_300_BW_1_2;    //FLRC bandwidth and bit rate, 1.3Mbs
const uint8_t CodingRate = FLRC_CR_1_0;                   //FLRC coding rate
const uint8_t BT = RADIO_MOD_SHAPING_BT_1_0;              //FLRC BT
const uint32_t Syncword = 0x54696761;                     //FLRC uses syncword

const int8_t TXpower  = 30;                                //power for transmissions in dBm
const uint16_t packet_delay = 100;                       //mS delay between packets

#define RXBUFFER_SIZE 127                               //Max RX buffer size  