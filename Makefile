PREFIX = ~/.micropython/lib

all:

# Installs all modules to a lib location, for development testing
install:
	@mkdir -p $(PREFIX)
	@if [ -n "$(MOD)" ]; then \
	    (cd $(MOD); cp -r * $(PREFIX)); \
	else \
	    for d in $$(find -maxdepth 1 -type d ! -name ".*"); do \
	        (cd $$d; cp -r * $(PREFIX)); \
	    done \
	fi
