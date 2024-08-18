import meshtastic
import meshtastic.tcp_interface

# Function to handle received messages
def on_receive(packet, interface):
    print(f"Received packet: {packet}")

# Initialize the TCP interface
try:
    print("Connecting to Meshtastic device at 192.168.200.177")
    interface = meshtastic.tcp_interface.TCPInterface(hostname="192.168.200.177")

    # Register the on_receive function as the callback
    interface.onReceive = on_receive

    print("Listening for messages on channel 2...")
    
    # Keep the script running
    while True:
        pass  # This keeps the script alive and listening for messages

except Exception as e:
    print(f"Error setting up Meshtastic interface: {e}")
