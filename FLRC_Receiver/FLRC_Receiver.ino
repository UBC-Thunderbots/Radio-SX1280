/*******************************************************************************************************
  Programs for Arduino - Copyright of the author Stuart Robinson - 29/09/21

  This program is supplied as is, it is up to the user of the program to decide if the program is
  suitable for the intended purpose and free from errors.
*******************************************************************************************************/


/*******************************************************************************************************
  Program Operation - This is a test receiver for the Fast Long Range Communication (FLRC) mode introduced
  in the SX128X devices. The program listens for incoming packets using the FLRC settings in the 'Settings.h'
  file. The pins to access the SX128X device need to be defined in the 'Settings.h' file also.

  There is a printout of the valid packets received, the packet is assumed to be in ASCII printable text,
  if its not ASCII text characters from 0x20 to 0x7F, expect weird things to happen on the Serial Monitor.
  The LED will flash for each packet received.

  Sample serial monitor output;

  3s  Hello World 1234567890*,CRC,DAAB,RSSI,-73dB,Length,23,Packets,1,Errors,0,IRQreg,6

  If there is a packet error it might look like this, which is showing a CRC error,

  6s PacketError,RSSI,-103dB,Length,119,Packets,3,Errors,1,IRQreg,46,IRQ_RX_DONE,IRQ_SYNCWORD_VALID,IRQ_CRC_ERROR

  Serial monitor baud rate is set at 9600.
*******************************************************************************************************/

#include <SPI.h>                                 //the lora device is SPI based so load the SPI library
#include <SX128XLT.h>                            //include the appropriate library   
#include "Settings.h"                            //include the setiings file, frequencies, LoRa settings etc   
#include <string>

SX128XLT LT;                                     //create a library class instance called LT

uint32_t RXpacketCount;
uint32_t errors;

uint8_t RXBUFFER[RXBUFFER_SIZE];                 //create the buffer that received packets are copied into
uint8_t TXBUFFER[RXBUFFER_SIZE];

uint8_t RXPacketL;                               //stores length of packet received
int16_t  PacketRSSI;                             //stores RSSI of received packet

uint8_t TXPacketL;
uint32_t TXPacketCount, startmS, endmS;

void loop()
{
  RXPacketL = LT.receive(RXBUFFER, RXBUFFER_SIZE, 10000, WAIT_RX); //wait for a packet to arrive with 10seconds (10000mS) timeout

  PacketRSSI = LT.readPacketRSSI();              //read the recived RSSI value

  if (RXPacketL == 0)                            //if the LT.receive() function detects an error, RXpacketL == 0
  {
    Serial.println("RXPacketL == 0");
    rx_packet_is_Error();
  }
  else
  {
    // transmit_back();
    rx_packet_is_OK();
  }

  // digitalWrite(LED1, LOW);                        //LED off

  Serial.println();
}

void transmit_back()
{
  Serial.print(TXpower);                                       //print the transmit power defined
  Serial.print(F("dBm "));
  Serial.print(F("Packet> "));
  Serial.flush();

  memcpy(TXBUFFER, RXBUFFER, RXBUFFER_SIZE);

  TXPacketL = sizeof(TXBUFFER);                                    //set TXPacketL to length of array
  TXBUFFER[0] = '!';
  TXBUFFER[TXPacketL - 1] = '*';                                   //replace null character at buffer end so its visible on reciver

  LT.printASCIIPacket(TXBUFFER, TXPacketL);                        //print the buffer (the sent packet) as ASCII

  startmS =  millis();                                         //start transmit timer
  TXPacketL = LT.transmit(TXBUFFER, TXPacketL, Timeout, TXpower, WAIT_TX);  //will return 0 if transmit fails, timeout 10 seconds

  if (TXPacketL > 0)
  {
    endmS = millis();                                          //packet sent, note end time
    TXPacketCount++;
    tx_packet_is_OK();
  }
  else
  {
    tx_packet_is_Error();                                 //transmit packet returned 0, so there was an error
  }

  Serial.println();
}

void tx_packet_is_OK()
{
  //if here packet has been sent OK
  uint16_t localCRC;

  Serial.print(F("  BytesSent,"));
  Serial.print(TXPacketL);                             //print transmitted packet length
  localCRC = LT.CRCCCITT(TXBUFFER, TXPacketL, 0xFFFF);
  Serial.print(F("  CRC,"));
  Serial.print(localCRC, HEX);                              //print CRC of sent packet
  Serial.print(F("  TransmitTime,"));
  Serial.print(endmS - startmS);                       //print transmit time of packet
  Serial.print(F("mS"));
  Serial.print(F("  PacketsSent,"));
  Serial.print(TXPacketCount);                         //print total of packets sent OK
}

void tx_packet_is_Error()
{
  //if here there was an error transmitting packet
  uint16_t IRQStatus;
  IRQStatus = LT.readIrqStatus();                  //read the the interrupt register
  Serial.print(F(" SendError,"));
  Serial.print(F("Length,"));
  Serial.print(TXPacketL);                         //print transmitted packet length
  Serial.print(F(",IRQreg,"));
  Serial.print(IRQStatus, HEX);                    //print IRQ status
  LT.printIrqStatus();                             //prints the text of which IRQs set
}

void rx_packet_is_OK()
{
  uint16_t IRQStatus, localCRC;

  IRQStatus = LT.readIrqStatus();                  //read the LoRa device IRQ status register

  RXpacketCount++;

  printElapsedTime();                              //print elapsed time to Serial Monitor
  Serial.print(F("  "));
  LT.printASCIIPacket(RXBUFFER, RXPacketL);        //print the packet as ASCII characters

  localCRC = LT.CRCCCITT(RXBUFFER, RXPacketL, 0xFFFF);  //calculate the CRC, this is the external CRC calculation of the RXBUFFER
  Serial.print(F(",CRC,"));                        //contents, not the LoRa device internal CRC
  Serial.print(localCRC, HEX);
  Serial.print(F(",RSSI,"));
  Serial.print(PacketRSSI);
  Serial.print(F("dB,Length,"));
  Serial.print(RXPacketL);
  Serial.print(F(",Packets,"));
  Serial.print(RXpacketCount);
  Serial.print(F(",Errors,"));
  Serial.print(errors);
  Serial.print(F(",IRQreg,"));
  Serial.print(IRQStatus, HEX);
}


void rx_packet_is_Error()
{
  uint16_t IRQStatus;
  IRQStatus = LT.readIrqStatus();                   //read the LoRa device IRQ status register

  printElapsedTime();                               //print elapsed time to Serial Monitor

  if (IRQStatus & IRQ_RX_TIMEOUT)                   //check for an RX timeout
  {
    Serial.print(F(" RXTimeout"));
  }
  else
  {
    errors++;
    Serial.print(F(" PacketError"));
    Serial.print(F(",RSSI,"));
    Serial.print(PacketRSSI);
    Serial.print(F("dB,Length,"));
    Serial.print(LT.readRXPacketL());               //get the real packet length
    Serial.print(F(",Packets,"));
    Serial.print(RXpacketCount);
    Serial.print(F(",Errors,"));
    Serial.print(errors);
    Serial.print(F(",IRQreg,"));
    Serial.print(IRQStatus, HEX);
    LT.printIrqStatus();                            //print the names of the IRQ registers set
  }


}


void printElapsedTime()
{
  float seconds;
  seconds = millis() / 1000;
  Serial.print(seconds, 0);
  Serial.print(F("s"));
}


void led_Flash(uint16_t flashes, uint16_t delaymS)
{
  uint16_t index;

  for (index = 1; index <= flashes; index++)
  {
    digitalWrite(LED1, HIGH);
    delay(delaymS);
    digitalWrite(LED1, LOW);
    delay(delaymS);
  }
}


void setup()
{
  Serial.begin(115200);
  Serial.println();
  Serial.println(F("53_FLRC_Receiver Starting"));
  Serial.println();

  SPI.begin();

  //SPI beginTranscation is normally part of library routines, but if it is disabled in the library
  //a single instance is needed here, so uncomment the program line below
  //SPI.beginTransaction(SPISettings(8000000, MSBFIRST, SPI_MODE0));

  //setup hardware pins used by device, then check if device is found
  if (LT.begin(NSS, NRESET, RFBUSY, DIO1, DIO2, DIO3, RX_EN, TX_EN, LORA_DEVICE))
  {
    Serial.println(F("FLRC Device found"));
    led_Flash(2, 125);
    delay(1000);
  }
  else
  {
    Serial.println(F("No FLRC device responding"));
    while (1)
    {
      // led_Flash(50, 50);                                       //long fast speed LED flash indicates device error
    }
  }


  // LT.setupFLRC(Frequency, Offset, BandwidthBitRate, CodingRate, BT, Syncword);

  //The full details of the setupFLRC function call above are listed below
  //***************************************************************************************************
  //Setup FLRC
  //***************************************************************************************************
  LT.setSleep(RETAIN_None);
  LT.setMode(MODE_STDBY_XOSC);
  LT.setRegulatorMode(USE_DCDC);
  LT.setPacketType(PACKET_TYPE_FLRC);
  LT.setRfFrequency(Frequency, Offset);
  LT.setBufferBaseAddress(0, 0);
  LT.setModulationParams(BandwidthBitRate, CodingRate, BT);
  LT.setPacketParams(PREAMBLE_LENGTH_16_BITS, FLRC_SYNC_WORD_LEN_P32S, RADIO_RX_MATCH_SYNCWORD_1, RADIO_PACKET_VARIABLE_LENGTH, 32, RADIO_CRC_OFF, RADIO_WHITENING_OFF);
  LT.setDioIrqParams(IRQ_RADIO_ALL, (IRQ_TX_DONE + IRQ_RX_TX_TIMEOUT), 0, 0);              //set for IRQ on TX done and timeout on DIO1
  LT.setSyncWord1(Syncword);
  LT.setSyncWordErrorTolerance(2);
  LT.setAutoFS(0x01);
  LT.setTxParams(TXpower, RADIO_RAMP_04_US);
  LT.setFS();
  LT.clearIrqStatus(IRQ_RADIO_ALL);  
  //***************************************************************************************************
  LT.setFLRCPayloadLengthReg(32);                             //FLRC will filter packets on receive according to length, so set to longest packet
  Serial.println();
  LT.printModemSettings();                                     //reads and prints the configured modem settings, useful check
  Serial.println();
  LT.printOperatingSettings();                                 //reads and prints the configured operting settings, useful check
  Serial.println();
  Serial.println();
  LT.printRegisters(0x900, 0x9FF);                             //print contents of device registers
  Serial.println();
  Serial.println();

  Serial.print(F("Receiver ready - RXBUFFER_SIZE "));
  Serial.println(RXBUFFER_SIZE);
  Serial.println();
}
