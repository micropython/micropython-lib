metadata(version="0.5.1")

require("re", unix_ffi=True)
require("base64")
require("binascii")
require("functools")
require("string")
# require("calendar") TODO
require("abc")
require("email.errors", unix_ffi=True)
require("email.header", unix_ffi=True)
require("email.charset", unix_ffi=True)
require("email.utils", unix_ffi=True)

package("email")
