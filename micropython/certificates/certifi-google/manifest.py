metadata(description="google CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("google.py",), base_path="../certifi", opt=3)
