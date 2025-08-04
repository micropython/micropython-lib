# uminio.py - A MicroPython library for uploading files to MinIO object storage.
#
# Based on the uboto3 library for AWS S3 by DanielMilstein.
# Modified to support self-hosted MinIO endpoints.
#
# MinIO Python client: https://github.com/minio/minio-py (for reference)
# Original uboto3: https://github.com/DanielMilstein/uboto3

import urequests
import uhashlib
import ubinascii
import utime
import ntptime

# --- MinIO Configuration ---
# IMPORTANT: Fill in these details for your MinIO server.
MINIO_ENDPOINT = "192.168.1.100:9000"  # Your MinIO server IP address and port
MINIO_ACCESS_KEY = "YOUR_ACCESS_KEY"  # Your MinIO access key
MINIO_SECRET_KEY = "YOUR_SECRET_KEY"  # Your MinIO secret key
MINIO_BUCKET = "micropython-uploads"  # The bucket you want to upload to
MINIO_USE_HTTPS = False  # Set to True if your MinIO server uses HTTPS

# MinIO is S3-compatible, but the signing process still requires a region.
# 'us-east-1' is a safe default that works for most MinIO setups.
MINIO_REGION = "us-east-1"


class MinioClient:
    """A client for interacting with MinIO object storage.
    This class provides methods to upload files to a specified bucket.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        region="us-east-1",
        use_https=False,
    ) -> None:
        """Initialize the MinIO client with the given parameters.

        :param endpoint: The MinIO server endpoint (IP:port).
        :param access_key: Your MinIO access key.
        :param secret_key: Your MinIO secret key.
        :param use_https: Whether to use HTTPS for requests.
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.use_https = use_https

    def _hmac_sha256(self, key_bytes, msg_bytes):
        """
        Calculates the HMAC-SHA256 hash.
        """
        block_size = 64

        if len(key_bytes) > block_size:
            key_bytes = uhashlib.sha256(key_bytes).digest()

        if len(key_bytes) < block_size:
            key_bytes = key_bytes + b"\x00" * (block_size - len(key_bytes))

        o_key_pad = bytes(b ^ 0x5C for b in key_bytes)
        i_key_pad = bytes(b ^ 0x36 for b in key_bytes)

        inner_hash = uhashlib.sha256(i_key_pad + msg_bytes).digest()
        outer_hash = uhashlib.sha256(o_key_pad + inner_hash).digest()

        return outer_hash

    def _get_timestamp(self) -> tuple[str, str]:
        """
        Generates the required timestamp strings for the signature.
        """
        now = utime.gmtime()
        amz_date = "{:04d}{:02d}{:02d}T{:02d}{:02d}{:02d}Z".format(
            now[0], now[1], now[2], now[3], now[4], now[5]
        )
        datestamp = "{:04d}{:02d}{:02d}".format(now[0], now[1], now[2])
        return amz_date, datestamp

    def _get_signature_key(self, date_stamp_string, service_name_string="s3"):
        """
        Derives the signing key from the secret key.
        """
        k_secret_bytes = ("AWS4" + self.secret_key).encode("utf-8")
        k_date_bytes = self._hmac_sha256(
            k_secret_bytes, date_stamp_string.encode("utf-8")
        )
        k_region_bytes = self._hmac_sha256(k_date_bytes, self.region.encode("utf-8"))
        k_service_bytes = self._hmac_sha256(
            k_region_bytes, service_name_string.encode("utf-8")
        )
        k_signing_bytes = self._hmac_sha256(k_service_bytes, b"aws4_request")
        return k_signing_bytes

    def sync_time(self) -> None:
        """
        Synchronizes the device's real-time clock with an NTP server.
        This is crucial for generating a valid signature.
        """
        print("Synchronizing time with NTP server...")
        try:
            ntptime.settime()  # This sets the device's RTC to UTC
            print("Time synchronized successfully.")
            now_utc = utime.gmtime()
            print(
                "Current UTC from device: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                    now_utc[0],
                    now_utc[1],
                    now_utc[2],
                    now_utc[3],
                    now_utc[4],
                    now_utc[5],
                )
            )
        except Exception as e:
            print(f"Error synchronizing time: {e}")

    def upload_file(
        self,
        local_file_path: str,
        bucket: str,
        object_name: str,
        content_type="application/octet-stream",
    ):
        """
        Uploads a file to a MinIO bucket using AWS Signature V4.

        :param local_file_path: The path to the local file to upload.
        :param bucket: The name of the MinIO bucket to upload to.
        :param object_name: The name of the object as it will be stored in MinIO.
        :param content_type: The MIME type of the file.
        :return: True if upload was successful (HTTP 200), False otherwise.
        """
        try:
            with open(local_file_path, "rb") as f:
                data = f.read()
            print(f"Successfully read {len(data)} bytes from {local_file_path}")
        except OSError as e:
            print(f"Error opening or reading file '{local_file_path}': {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred reading file '{local_file_path}': {e}")
            return False

        # The 'host' for MinIO is just the endpoint.
        host = self.endpoint
        amz_date, datestamp = self._get_timestamp()
        service = "s3"

        # ---- Task 1: Create Canonical Request ----
        # For MinIO, the canonical URI must include the bucket name.
        method = "PUT"
        canonical_uri = f"/{bucket}/{object_name}"
        canonical_querystring = ""

        payload_hash_bytes = uhashlib.sha256(data).digest()
        payload_hash_hex = ubinascii.hexlify(payload_hash_bytes).decode()

        # Headers must be in alphabetical order by lowercase header name.
        canonical_headers_list = [
            ("host", host),
            ("x-amz-content-sha256", payload_hash_hex),
            ("x-amz-date", amz_date),
        ]
        canonical_headers_list.sort(key=lambda item: item[0])

        canonical_headers_str = ""
        signed_headers_list = []
        for key, value in canonical_headers_list:
            canonical_headers_str += f"{key}:{value.strip()}\n"
            signed_headers_list.append(key)
        signed_headers_str = ";".join(signed_headers_list)

        canonical_request = (
            f"{method}\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers_str}\n"
            f"{signed_headers_str}\n"
            f"{payload_hash_hex}"
        )

        # ---- Task 2: Create String to Sign ----
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{datestamp}/{self.region}/{service}/aws4_request"

        hashed_canonical_request_bytes = uhashlib.sha256(
            canonical_request.encode("utf-8")
        ).digest()
        hashed_canonical_request_hex = ubinascii.hexlify(
            hashed_canonical_request_bytes
        ).decode()

        string_to_sign = (
            f"{algorithm}\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashed_canonical_request_hex}"
        )

        # ---- Task 3: Calculate Signature ----
        signing_key_bytes = self._get_signature_key(datestamp, service)
        signature_bytes = self._hmac_sha256(
            signing_key_bytes, string_to_sign.encode("utf-8")
        )
        signature_hex = ubinascii.hexlify(signature_bytes).decode()

        # ---- Task 4: Add Signing Information to the Request ----
        authorization_header = (
            f"{algorithm} "
            f"Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers_str}, "
            f"Signature={signature_hex}"
        )

        headers = {
            "Host": host,
            "X-Amz-Date": amz_date,
            "X-Amz-Content-Sha256": payload_hash_hex,
            "Authorization": authorization_header,
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
        }

        # ---- Make the PUT request ----
        protocol = "https" if self.use_https else "http"
        url = f"{protocol}://{host}{canonical_uri}"
        print(f"Uploading to: {url}")

        try:
            response = urequests.put(url, headers=headers, data=data)
            print(f"Response Status: {response.status_code}")
            print(f"Response Text: {response.text}")
            response.close()
            return response.status_code == 200
        except Exception as e:
            print(f"Error during MinIO PUT request: {e}")
            return False
