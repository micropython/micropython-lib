metadata(description="godaddy CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("godaddy.py",), base_path="../certifi", opt=3)
