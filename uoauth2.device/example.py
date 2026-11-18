from uoauth2.device import DeviceAuth

# For more information on how to create clients 
# Look at: https://developers.google.com/identity/protocols/oauth2/limited-input-device

device_auth = DeviceAuth(
    client_id='648445354032-mv5p4b09hcj0116v57pnkmp42fn8m220.apps.googleusercontent.com',
    client_secret='9aeN3LGr0yq4TYjwGcfUVJKo',
    discovery_endpoint='https://accounts.google.com/.well-known/openid-configuration',
    scopes=list(['openid'])
)

# Discover OpenID endpoints
device_auth.discover()

# Start authorization process
device_auth.authorize()

# Use the user-code and verification URL to show some UI to the user
# To complete the authorization process.
user_code = device_auth.user_code
verification_url = device_auth.verification_url

print(user_code, verification_url)

# Check for completed authorization
device_auth.check_authorization_complete()

# Fetch a valid access token
print(device_auth.token())
