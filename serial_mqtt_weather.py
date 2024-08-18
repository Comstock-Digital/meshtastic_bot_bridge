import time
import sys
import subprocess  # This import was missing
from pubsub import pub
import paho.mqtt.client as mqtt
from meshtastic.serial_interface import SerialInterface
from meshtastic import portnums_pb2

serial_port = '/dev/cu.usbserial-0001'  # Replace with your Meshtastic device's serial port

# MQTT Broker details
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "meshtastic/weather"
JSON_TOPIC = "msh/US/meshtastic/to_mesh"
FROM_MESH_TOPIC = "meshtastic/from_mesh"
MESHTASTIC_CHANNEL_INDEX = 2
BROADCAST_ID = 4294967295

# MQTT Authentication details
MQTT_USERNAME = "username"
MQTT_PASSWORD = "password"

def get_weather(city_name):
    """Fetch weather information for the specified city."""
    try:
        city_name_formatted = city_name.replace(" ", "+")
        result = subprocess.run(
            ["curl", "-s", f"wttr.in/{city_name_formatted}?format=3"],
            stdout=subprocess.PIPE,
            text=True
        )
        weather_output = result.stdout.strip()
        print(f"Weather command output: '{weather_output}'")
        return weather_output
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return f"Error fetching weather: {e}"

def send_to_meshtastic(message, channel_index):
    """Send the message to the specified channel on the Meshtastic network."""
    global interface
    try:
        if not interface:
            interface = SerialInterface(serial_port)
        
        interface.sendText(message, destinationId=BROADCAST_ID, channelIndex=channel_index)
        print(f"Message '{message}' sent to Meshtastic channel {channel_index}")
        time.sleep(1)
    except Exception as e:
        print(f"Error sending message to Meshtastic: {e}")

def get_node_info(serial_port):
    print("Initializing SerialInterface to get node info...")
    local = SerialInterface(serial_port)
    node_info = local.nodes
    local.close()
    print("Node info retrieved.")
    return node_info

def parse_node_info(node_info):
    print("Parsing node info...")
    nodes = []
    for node_id, node in node_info.items():
        nodes.append({
            'num': node_id,
            'user': {
                'shortName': node.get('user', {}).get('shortName', 'Unknown')
            }
        })
    print("Node info parsed.")
    return nodes

def on_receive(packet, interface, node_list):
    try:
        if packet['decoded']['portnum'] == portnums_pb2.TEXT_MESSAGE_APP:
            message = packet['decoded']['payload'].decode('utf-8')
            fromnum = packet['fromId']
            shortname = next((node['user']['shortName'] for node in node_list if node['num'] == fromnum), 'Unknown')
            print(f"{shortname}: {message}")
            if message.lower().startswith("!weather "):
                city_name = message[len("!weather "):].strip()
                weather_info = get_weather(city_name)
                send_to_meshtastic(weather_info, MESHTASTIC_CHANNEL_INDEX)
    except KeyError:
        pass  # Ignore KeyError silently
    except UnicodeDecodeError:
        pass  # Ignore UnicodeDecodeError silently

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)
    client.subscribe(JSON_TOPIC)
    client.subscribe(FROM_MESH_TOPIC)
    print(f"Subscribed to MQTT topics: {MQTT_TOPIC}, {JSON_TOPIC}, {FROM_MESH_TOPIC}")

def on_message(client, userdata, msg):
    message_text = msg.payload.decode().strip()
    print(f"Received message: '{message_text}' on topic {msg.topic}")
    if msg.topic == MQTT_TOPIC:
        if message_text.lower().startswith("!weather "):
            city_name = message_text[len("!weather "):].strip()
            weather_info = get_weather(city_name)
            send_to_meshtastic(weather_info, MESHTASTIC_CHANNEL_INDEX)
        else:
            print(f"Ignored message: {message_text}")

def main():
    print(f"Using serial port: {serial_port}")

    # Retrieve and parse node information
    node_info = get_node_info(serial_port)
    node_list = parse_node_info(node_info)

    # Print node list for debugging
    print("Node List:")
    for node in node_list:
        print(node)

    # Subscribe the callback function to message reception
    def on_receive_wrapper(packet, interface):
        on_receive(packet, interface, node_list)

    pub.subscribe(on_receive_wrapper, "meshtastic.receive")
    print("Subscribed to meshtastic.receive")

    # Set up the SerialInterface for message listening
    global interface
    interface = SerialInterface(serial_port)
    print("SerialInterface setup for listening.")

    # Set up MQTT client
    client = mqtt.Client(protocol=mqtt.MQTTv5)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to MQTT broker
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")

    # Start MQTT loop in a separate thread
    try:
        client.loop_start()
    except Exception as e:
        print(f"Error starting MQTT loop: {e}")

    # Keep the script running to listen for messages
    try:
        while True:
            sys.stdout.flush()
            time.sleep(1)  # Sleep to reduce CPU usage
    except KeyboardInterrupt:
        print("Script terminated by user")
        interface.close()

if __name__ == "__main__":
    main()
