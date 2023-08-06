metadata(description="LCD160CR driver.", version="0.1.0")

options.defaults(test=False)

module("lcd160cr.py", opt=3)

if options.test:
    module("lcd160cr_test.py", opt=3)
