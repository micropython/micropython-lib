metadata(description="isrg CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("isrg.py",), base_path="../certifi", opt=3)
