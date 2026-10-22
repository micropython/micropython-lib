metadata(description="sectigo CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("sectigo.py",), base_path="../certifi", opt=3)
