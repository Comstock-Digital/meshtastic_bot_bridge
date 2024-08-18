import paho.mqtt.client as mqtt
import meshtastic
import meshtastic.tcp_interface
import time
import subprocess
import json

# MQTT Broker details
MQTT_BROKER = "localhost"  # Set to your broker's address
MQTT_PORT = 1883
MQTT_TOPIC = "meshtastic/weather"  # Topic to listen to for weather requests via MQTT
JSON_TOPIC = "msh/US/meshtastic/to_mesh"  # Topic for JSON messages from Meshtastic
FROM_MESH_TOPIC = "meshtastic/from_mesh"  # Topic for messages from the mesh

# Authentication details for MQTT (if required)
MQTT_USERNAME = "username"
MQTT_PASSWORD = "password"

# Meshtastic TCP interface
MESHTASTIC_HOST = "192.168.200.7"  # IP address of your Meshtastic device
MESHTASTIC_CHANNEL_INDEX = 2  # Channel index to send the weather response to
BROADCAST_ID = 4294967295  # Meshtastic broadcast ID (0xFFFFFFFF)

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
        return f"Error fetching weather: {e}"

def send_to_meshtastic(message, channel_index):
    """Send the message to the specified channel on the Meshtastic network."""
    try:
        interface = meshtastic.tcp_interface.TCPInterface(hostname=MESHTASTIC_HOST)
        interface.sendText(message, destinationId=BROADCAST_ID, channelIndex=channel_index)
        print(f"Message '{message}' sent to Meshtastic channel {channel_index}")
        time.sleep(1)
        interface.close()
    except Exception as e:
        print(f"Error sending message to Meshtastic: {e}")

def on_receive_json(message_text):
    """Handle incoming JSON messages from the Meshtastic network."""
    try:
        packet = json.loads(message_text)
        decoded = packet.get('decoded', {}).get('payload', '').strip()
        print(f"Decoded message: '{decoded}'")
        if decoded.lower().startswith("!weather "):
            city_name = decoded[len("!weather "):].strip()
            weather_info = get_weather(city_name)
            send_to_meshtastic(weather_info, MESHTASTIC_CHANNEL_INDEX)
        else:
            print(f"Ignored message: {decoded}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Error processing JSON message: {e}")

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
        if message_text.lower().startswith("weather in "):
            city_name = message_text[len("weather in "):].strip()
            weather_info = get_weather(city_name)
            send_to_meshtastic(weather_info, MESHTASTIC_CHANNEL_INDEX)
        elif message_text.lower().startswith("!weather "):
            city_name = message_text[len("!weather "):].strip()
            weather_info = get_weather(city_name)
            send_to_meshtastic(weather_info, MESHTASTIC_CHANNEL_INDEX)
        else:
            print(f"Ignored message: {message_text}")
    elif msg.topic == JSON_TOPIC or msg.topic == FROM_MESH_TOPIC:
        on_receive_json(message_text)

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

# Meshtastic TCP interface
try:
    interface = meshtastic.tcp_interface.TCPInterface(hostname=MESHTASTIC_HOST)
    print("Meshtastic listener started.")
    while True:
        time.sleep(1)
except Exception as e:
    print(f"Error setting up Meshtastic interface: {e}")
finally:
    client.loop_stop()
    if interface:
        interface.close()
