PREFIX = ~/.micropython/lib

all:

# Installs all modules to a lib location, for development testing
install:
	@./install_modules.py -d ${PREFIX} $(MOD)
