metadata(description="digicert CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("digicert.py",), base_path="../certifi", opt=3)
