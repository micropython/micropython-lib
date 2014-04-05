PREFIX = ~/.micropython/lib

all:

# Installs all modules to a lib location, for development testing
install:
	mkdir -p $(PREFIX)
	for d in $$(find -maxdepth 1 -type d ! -name ".*"); do \
	    (cd $$d; cp -r $$(find . -name "*.py") $(PREFIX)); \
	done \
