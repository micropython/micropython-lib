metadata(description="globalsign CA certificates.", version="0.0.1")

require("certifi")

package("certifi", files=("globalsign.py",), base_path="../certifi", opt=3)
