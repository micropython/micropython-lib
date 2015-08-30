all:

# This target prepares snapshot of all dependency modules, for
# self-contained install
deps: upip_ffilib.py upip_os.py upip_os_path.py upip_errno.py upip_gzip.py upip_stat.py upip_utarfile.py

upip_ffilib.py: ../ffilib/ffilib.py
	cp $^ $@
upip_os.py: ../os/os/__init__.py
	sed -r -e 's/((ffilib|errno|stat)([^_"]|$$))/upip_\1/' $^ >$@
upip_os_path.py: ../os.path/os/path.py
	sed -r -e 's/((ffilib|errno|os|stat)([^_"]|$$))/upip_\1/' $^ >$@
upip_errno.py: ../errno/errno.py
	cp $^ $@
upip_gzip.py: ../gzip/gzip.py
	cp $^ $@
upip_stat.py: ../stat/stat.py
	cp $^ $@
upip_utarfile.py: ../utarfile/utarfile.py
	cp $^ $@

clean:
	rm upip_*.py
