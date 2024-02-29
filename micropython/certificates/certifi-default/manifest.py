metadata(description="default CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("default.py",), base_path="../certifi", opt=3)
