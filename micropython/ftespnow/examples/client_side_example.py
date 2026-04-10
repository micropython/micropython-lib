import ftespnow

# Initialize ESP-NOW client
esp = ftespnow.CLIENT()

# Connect to ESP-NOW server
esp.connect("a4f00f772d15") # Change to actual server mac address

# Send a message
message = "Hello"
sent = esp.send_message(message)
if sent: # Check if server received the data
    print("Message received by server")
else:
    print("Message not received by server")

# Receive a message
received_data = esp.receive_message()
if received_data == None: # Check if any data was received
    print("No message was received (timed out)")
else:
    print(f"Here is the received data: {received_data}")

# Send a .txt file
txt_sent = esp.send_txt("filepath/filename.txt")
if txt_sent: # Check if server received the data
    print("File received by server")
else:
    print("File not received by server")

# Send a .json file
json_sent = esp.send_json("filepath/filename.json")
if json_sent: # Check if server received the data
    print("File received by server")
else:
    print("File not received by server")

# Write received data to .txt file
txt_received = esp.receive_to_txt("filepath/filename.txt", mode='w') # Set mode to 'w' so file is truncated before writing
if txt_received:
    print("File received successfully")
else:
    print("No file received. Destination file was not created/modified")

# Write received data to .json file
json_received = esp.receive_to_json("filepath/filename.json", mode='w') # Set mode to 'w' so file is truncated before writing
if json_received:
    print("File received successfully")
else:
    print("No file received. Destination file was not created/modified")

# Write received data to a python dictionary
data_dict = esp.receive_to_dict()
print(data_dict)