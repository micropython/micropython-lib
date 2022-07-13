metadata(version="0.5.3")

require("re", unix_ffi=True)
require("uu")
require("base64")
require("binascii")
require("email.utils", unix_ffi=True)
require("email.errors", unix_ffi=True)
require("email.charset", unix_ffi=True)

package("email")
