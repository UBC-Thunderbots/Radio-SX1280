import serial
import time

# Replace 'COM6' with the COM port your ESP32 is connected to
serialPort = serial.Serial(port="COM6", baudrate=115200, timeout=2)

iterations = 10

def measure_latency(iterations):
    rtts = []  # List to store round-trip times for each iteration

    for _ in range(iterations):
        # Send a command to the ESP32
        message = "PING\n"  # Ensure this matches the command expected by the ESP32
        serialPort.write(message.encode())

        # Record the send time in microseconds
        send_time = int(time.time() * 1_000_000)

        # Wait for the reply
        while True:
            if serialPort.inWaiting() > 0:
                incomingMessage = serialPort.readline().decode().strip()
                if incomingMessage == "PONG":
                    # Record the receive time in microseconds
                    receive_time = int(time.time() * 1_000_000)
                    # Calculate round-trip time
                    rtt = receive_time - send_time
                    rtts.append(rtt)  # Add the RTT to the list
                    print(f"Round-Trip Time: {rtt} microseconds")
                    break  # Exit the loop to start the next iteration
                else:
                    print(f"Received unexpected message: {incomingMessage}")
                    break  # Consider adding logic to handle unexpected messages properly

    return rtts

# Measure latency for 10 iterations
rtt_results = measure_latency(iterations)
print("RTT measurements (in microseconds):", rtt_results)
print("RTT average (in microseconds):", sum(rtt_results)/iterations)
print("One way average estimate (in microseconds):", (sum(rtt_results)/iterations)/2)

# Close the serial port
serialPort.close()
