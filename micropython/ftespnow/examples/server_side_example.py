import ftespnow

# Initialize ESP-NOW client
esp = ftespnow.SERVER()

# Send a message
message = "Hello"
peer = "a4f00f772d15"  # Mac address of the client that you want to send data to
sent = esp.send_message(peer, message)
if sent: # Check if client received the data
    print("Message received by clientclient")
else:
    print("Message not received by client")

# Receive a message
received_data = esp.receive_message()
if received_data is None:  # Check if any data was received
    print("No message was received (timed out)")
else:
    print(f"Here is the received data: {received_data}")

# Send a .txt file
txt_sent = esp.send_txt(peer, "filepath/filename.txt")
if txt_sent:  # Check if client received the data
    print("File received by client")
else:
    print("File not received by client")

# Send a .json file
json_sent = esp.send_json(peer, "filepath/filename.json")
if json_sent:  # Check if client received the data
    print("File received by client")
else:
    print("File not received by client")

# Write received data to .txt file
txt_received = esp.receive_to_txt(
    "filepath/filename.txt", mode="w"
    )  # Set mode to 'w' so file is truncated before writing
if txt_received:
    print("File received successfully")
else:
    print("No file received. Destination file was not created/modified")

# Write received data to .json file
json_received = esp.receive_to_json(
    "filepath/filename.json", mode="w"
    )  # Set mode to 'w' so file is truncated before writing
if json_received: # Check if any data was received
    print("File received successfully")
else:
    print("No file received. Destination file was not created/modified")

# Write received data to a python dictionary
data_dict = esp.receive_to_dict()  # Will return {} if no data was received
print(data_dict)
