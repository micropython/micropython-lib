metadata(description="amazon CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("amazon.py",), base_path="../certifi", opt=3)
