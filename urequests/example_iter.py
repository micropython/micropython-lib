# Example of processing large responses, the response is automatically closed
try:
    import urequests as requests
except ImportError:
    import requests

# Iterate over individual lines of the response
with requests.get('http://jsonplaceholder.typicode.com/users') as response:
    for line in response.iter_lines():
	    print(line.decode(response.encoding))
		
# Iterate over 'chunks' of the response
with requests.get('http://jsonplaceholder.typicode.com/users') as response:
    for chunk in response.iter_content():
	    print(chunk.decode(response.encoding))
