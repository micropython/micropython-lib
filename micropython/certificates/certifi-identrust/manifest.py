metadata(description="identrust CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("identrust.py",), base_path="../certifi", opt=3)
