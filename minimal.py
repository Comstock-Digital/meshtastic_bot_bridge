import paho.mqtt.client as mqtt
import meshtastic
import meshtastic.tcp_interface
import time
import json

# Configuration
MESHTASTIC_HOST = "192.168.200.177"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
JSON_TOPIC = "msh/2/json/#"  # Wildcard to listen to all JSON topics

def on_receive_json(packet_json):
    """Handle JSON packets."""
    print(f"Received JSON packet: {packet_json}")
    try:
        packet = json.loads(packet_json)
        print(f"Decoded packet: {packet}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(JSON_TOPIC)
    print(f"Subscribed to JSON topic: {JSON_TOPIC}")

def on_message(client, userdata, msg):
    message_text = msg.payload.decode().strip()
    print(f"Received message on {msg.topic}: {message_text}")
    on_receive_json(message_text)

def main():
    try:
        # Set up MQTT client
        client = mqtt.Client(protocol=mqtt.MQTTv5)
        client.on_connect = on_connect
        client.on_message = on_message

        # Connect to MQTT broker
        client.username_pw_set("username", "password")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        # Set up Meshtastic TCP interface
        interface = meshtastic.tcp_interface.TCPInterface(hostname=MESHTASTIC_HOST)
        print("Meshtastic listener started.")

        # Keep the script running
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if interface:
            interface.close()
            print("Disconnected from Meshtastic device.")
        client.loop_stop()

if __name__ == "__main__":
    main()
