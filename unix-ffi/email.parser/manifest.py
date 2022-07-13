metadata(version="0.5.1")

require("warnings")
require("email.feedparser", unix_ffi=True)
require("email.message", unix_ffi=True)
require("email.internal", unix_ffi=True)

package("email")
