import paho.mqtt.client as mqtt

# Define the on_connect function to handle the connection to the MQTT broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("#")  # Subscribe to all topics

# Define the on_message function to handle incoming messages
def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}, Message: {msg.payload.decode()}")

# Create a new MQTT client instance with the latest protocol version
client = mqtt.Client(protocol=mqtt.MQTTv311)  # Updated to MQTT v3.1.1 to avoid deprecation warnings
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect("localhost", 1883, 60)

# Start the loop to listen for messages
client.loop_forever()
