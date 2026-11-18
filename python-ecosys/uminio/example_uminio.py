import network
import time
from uminio import MinioClient

# --- MinIO Client Configuration ---
MINIO_ENDPOINT = "192.168.1.100:9000"  # Your MinIO server IP address and port
MINIO_ACCESS_KEY = "YOUR_ACCESS_KEY"  # Your MinIO access key
MINIO_SECRET_KEY = "YOUR_SECRET_KEY"  # Your MinIO secret key
MINIO_REGION = "eu-east-1"  # The region for your MinIO server
MINIO_USE_HTTPS = False  # Set to True if your MinIO server uses HTTPS

mc = MinioClient(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    region=MINIO_REGION,
    use_https=MINIO_USE_HTTPS,
)
# --- Network Configuration (Example for ESP32/ESP8266) ---
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"


def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Connecting to WiFi...")
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        while not sta_if.isconnected():
            time.sleep(1)
    print("Network Config:", sta_if.ifconfig())


# --- Main Application ---
def main():
    # 1. Connect to WiFi
    connect_wifi()

    # 2. Synchronize time (critical for MinIO authentication)
    mc.sync_time()

    # 3. Create a dummy file to upload (or use an existing file)
    local_file_to_upload = "data.txt"
    bucket_name = "my_bucket"  # Ensure this bucket exists in MinIO
    s3_object_name = "my_device_data/data.txt"  # Desired path and name in S3
    content_type = "text/plain"

    try:
        with open(local_file_to_upload, "w") as f:
            f.write("Hello from MicroPython!\n")
            f.write(f"Timestamp: {time.time()}\n")
        print(f"Created dummy file: {local_file_to_upload}")
    except OSError as e:
        print(f"Error creating file: {e}")
        return

    # 4. Upload the file
    print(
        f"Attempting to upload '{local_file_to_upload}' to MinIO bucket '{bucket_name}' as '{s3_object_name}'..."
    )
    if mc.upload_file(local_file_to_upload, bucket_name, s3_object_name, content_type):
        print("Upload successful!")
    else:
        print("Upload failed.")


if __name__ == "__main__":
    main()
