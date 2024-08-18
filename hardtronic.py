import meshtastic
import meshtastic.tcp_interface
import json
import time

# Configuration
MESHTASTIC_HOST = "192.168.200.177"  # IP address of your Meshtastic device

# Connect to Meshtastic device using TCPInterface
print(f"Connecting to Meshtastic device at {MESHTASTIC_HOST}")

try:
    interface = meshtastic.tcp_interface.TCPInterface(hostname=MESHTASTIC_HOST)
except Exception as e:
    print(f"Error connecting to Meshtastic device: {e}")
    exit(1)

print("Listening for messages on all channels...")

def on_receive(packet, interface):
    """Callback function to handle incoming messages."""
    print(f"Received packet: {json.dumps(packet, indent=2)}")

try:
    # Attach the on_receive callback
    interface.onReceive = on_receive
    
    # Keep the script running to listen to messages
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping the listener...")
finally:
    interface.close()
    print("Connection to Meshtastic device closed.")
