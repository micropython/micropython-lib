
VERSION ?=0.0.1

certifi: ca-bundle.crt ca_bundle_mp.py
	./make-certifi.py $(VERSION) 

ca-bundle.crt:
	./mk-ca-bundle.pl 
	rm certdata.txt

ca_bundle_mp.py: ca-bundle.crt cmn_crt_authorities.csv 
	./make-ca-bundle.py ca-bundle.crt cmn_crt_authorities.csv

cmn_crt_authorities.csv:
	echo cmn_crt_authorities.csv

clean:
	rm ca-bundle.crt
	rm ca_bundle_mp.py

