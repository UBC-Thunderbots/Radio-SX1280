/*******************************************************************************************************
  Programs for Arduino - Copyright of the author Stuart Robinson - 29/09/21

  This program is supplied as is, it is up to the user of the program to decide if the program is
  suitable for the intended purpose and free from errors.
*******************************************************************************************************/


/*******************************************************************************************************
  Program Operation - This is a test transmitter for the Fast Long Range Communication (FLRC) mode
  introduced in the SX128X devices. A packet containing ASCII text is sent according to the frequency and
  FLRC settings specified in the 'Settings.h' file. The pins to access the SX128X device need to be defined
  in the 'Settings.h' file also.

  The details of the packet sent and any errors are shown on the Serial Monitor, together with the transmit
  power used, the packet length and the CRC of the packet. The matching receive program, '53_FLRC_Receiver'
  can be used to check the packets are being sent correctly, the frequency and FLRC settings (in Settings.h)
  must be the same for the Transmit and Receive program. Sample Serial Monitor output;

  10dBm Packet> {packet contents*}  BytesSent,23  CRC,DAAB  TransmitTime,54mS  PacketsSent,1

  Serial monitor baud rate is set at 9600
*******************************************************************************************************/

#include <SPI.h>       //the SX128X device is SPI based so load the SPI library
#include <SX128XLT.h>  //include the appropriate library
#include "Settings.h"  //include the setiings file, frequencies, LoRa settings etc

SX128XLT LT;  //create a library class instance called LT

//TX
uint8_t TXPacketL;
uint32_t TXPacketCount, startmS, endmS;

//RX
uint8_t RXBUFFER[RXBUFFER_SIZE];                 //create the buffer that received packets are copied into
uint8_t RXPacketL;                               //stores length of packet received
int16_t  PacketRSSI;                             //stores RSSI of received packet
uint32_t RXpacketCount;
uint32_t errors;

//User Input Variable
char userInput;
uint8_t buff[RXBUFFER_SIZE];

void loop() {
  Serial.print(TXpower);  //print the transmit power defined
  Serial.print(F("dBm "));
  Serial.print(F("Packet> "));
  Serial.flush();

  for (int i = 0; i < RXBUFFER_SIZE; ++i) {
    buff[i] = 'A';
  }

  TXPacketL = sizeof(buff);   //set TXPacketL to length of array
  buff[TXPacketL - 1] = '*';  //replace null character at buffer end so its visible on reciver

  LT.printASCIIPacket(buff, TXPacketL);  //print the buffer (the sent packet) as ASCII

  //digitalWrite(LED1, HIGH);
  startmS = millis();  //start transmit timer

  //User Input Logic
  Serial.println();
  Serial.print("Enter any key if you want to send a packet: Enter 1");
  userInput = 1;
  while(Serial.available() == 0){};
  userInput = Serial.parseInt();

  if(userInput == 1){

    //User Input Code
    Serial.println();
    Serial.print("You entered '1'. Proceeding...\n");
    Serial.println();

    for (int i = 0; i < 6; i++){
      buff[i] = 'B';

      TXPacketL = LT.transmit(buff, TXPacketL, 10000, TXpower, WAIT_TX);  //will return 0 if transmit fails, timeout 10 seconds
  
      if (TXPacketL > 0) {
        packet_is_OK_transmit();
      } else {
        packet_is_Error_transmit();  //transmit packet returned 0, so there was an error
      }

    }


    //Receiving Code
    Serial.println();
    Serial.print("Checking if received a return packet");
    Serial.println();

    RXPacketL = LT.receive(RXBUFFER, RXBUFFER_SIZE, 10000, WAIT_RX); //wait for a packet to arrive with 1seconds (1s) timeout
    PacketRSSI = LT.readPacketRSSI();              //read the recived RSSI value
    if (RXPacketL == 0)                            //if the LT.receive() function detects an error, RXpacketL == 0
    {
      packet_is_Error_recieve();
    }
    else
    {
      packet_is_OK_recieve();
    }
  
  

    Serial.println();

  }
  else{

    Serial.println();
    Serial.print("Exiting, failed to press 1");
    Serial.println();
    return;

  }
  

  //digitalWrite(LED1, LOW);
  Serial.println();
  delay(packet_delay);  //have a delay between packets
}


void packet_is_OK_transmit() {
  //if here packet has been sent OK
  uint16_t localCRC;

  Serial.print(F("  BytesSent,"));
  Serial.print(TXPacketL);  //print transmitted packet length
  localCRC = LT.CRCCCITT(buff, TXPacketL, 0xFFFF);
  Serial.print(F("  CRC,"));
  Serial.print(localCRC, HEX);  //print CRC of sent packet
  Serial.print(F("  TransmitTime,"));
  Serial.print(endmS - startmS);  //print transmit time of packet
  Serial.print(F("mS"));
  Serial.print(F("  PacketsSent,"));
  Serial.print(TXPacketCount);  //print total of packets sent OK
}


void packet_is_Error_transmit() {
  //if here there was an error transmitting packet
  uint16_t IRQStatus;
  IRQStatus = LT.readIrqStatus();  //read the the interrupt register
  Serial.print(F(" SendError,"));
  Serial.print(F("Length,"));
  Serial.print(TXPacketL);  //print transmitted packet length
  Serial.print(F(",IRQreg,"));
  Serial.print(IRQStatus, HEX);  //print IRQ status
  LT.printIrqStatus();           //prints the text of which IRQs set
}

void packet_is_OK_recieve()
{
  uint16_t IRQStatus, localCRC;

  IRQStatus = LT.readIrqStatus();                  //read the LoRa device IRQ status register

  RXpacketCount++;

  //printElapsedTime();                              //print elapsed time to Serial Monitor
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

void packet_is_Error_recieve()
{
  uint16_t IRQStatus;
  IRQStatus = LT.readIrqStatus();                   //read the LoRa device IRQ status register

  //printElapsedTime();                               //print elapsed time to Serial Monitor

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

void led_Flash(uint16_t flashes, uint16_t delaymS) {
  uint16_t index;
  for (index = 1; index <= flashes; index++) {
    digitalWrite(LED1, HIGH);
    delay(delaymS);
    digitalWrite(LED1, LOW);
    delay(delaymS);
  }
}


void setup() {
  //pinMode(LED1, OUTPUT);                                   //setup pin as output for indicator LED
  //led_Flash(2, 125);                                       //two quick LED flashes to indicate program start

  Serial.begin(115200);
  Serial.println();
  Serial.println(F("52_FLRC_Transmitter Starting"));

  SPI.begin();

  //SPI beginTranscation is normally part of library routines, but if it is disabled in library
  //a single instance is needed here, so uncomment the program line below
  //SPI.beginTransaction(SPISettings(8000000, MSBFIRST, SPI_MODE0));

  //setup hardware pins used by device, then check if device is found
  if (LT.begin(NSS, NRESET, RFBUSY, DIO1, RX_EN, TX_EN, LORA_DEVICE)) {
    Serial.println(F("FLRC Device found"));
    led_Flash(2, 125);  //two further quick LED flashes to indicate device found
    delay(1000);
  } else {
    Serial.println(F("No FLRC device responding"));
    while (1) {
      led_Flash(50, 50);  //long fast speed LED flash indicates device error
    }
  }

  //LT.setupFLRC(Frequency, Offset, BandwidthBitRate, CodingRate, BT, Syncword);

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
  LT.setPacketParams(PREAMBLE_LENGTH_08_BITS, FLRC_SYNC_WORD_LEN_P32S, RADIO_RX_MATCH_SYNCWORD_1, RADIO_PACKET_VARIABLE_LENGTH, RXBUFFER_SIZE, RADIO_CRC_OFF, RADIO_WHITENING_OFF);
  LT.setDioIrqParams(IRQ_RADIO_ALL, (IRQ_TX_DONE + IRQ_RX_TX_TIMEOUT), 0, 0);  //set for IRQ on TX done and timeout on DIO1
  LT.setSyncWord1(Syncword);
  LT.setSyncWordErrorTolerance(2);
  LT.setAutoFS(0x01);
  LT.setTxParams(TXpower, RADIO_RAMP_04_US);
  LT.setFS();
  LT.clearIrqStatus(IRQ_RADIO_ALL);  
  //***************************************************************************************************

  Serial.println();
  LT.printModemSettings();  //reads and prints the configured modem settings, useful check
  Serial.println();
  LT.printOperatingSettings();  //reads and prints the configured operating settings, useful check
  Serial.println();
  Serial.println();
  LT.printRegisters(0x900, 0x9FF);  //print contents of device registers
  Serial.println();
  Serial.println();

  Serial.print(F("Transmitter ready"));
  Serial.println();
}
