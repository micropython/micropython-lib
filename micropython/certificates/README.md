
## MicroPython Certifi

This is an approach to include Root CA certificates from the most common Certificate Authorities following 

current [ssl certificates usage statistics](https://w3techs.com/technologies/overview/ssl_certificate)

### Ca-bundle Instructions
---------------------
#### 1. Download ca-bundle.crt
`ca-bundle.crt` is obtained using *curl's* script `mk-ca-bundle.pl` from [curl](https://github.com/curl/curl) repo in `curl/scripts` dir, 
which obtains the certificates from [mozilla's CA store](https://www.mozilla.org/en-US/about/governance/policies/security-group/certs/policy/). 

```console
$ ./mk-ca-bundle.pl
SHA256 of old file: 0
Downloading certdata.txt ...
Get certdata with curl!
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 1278k  100 1278k    0     0   264k      0  0:00:04  0:00:04 --:--:--  264k
Downloaded certdata.txt
SHA256 of new file: 90c470e705b4b5f36f09684dc50e2b79c8b86989a848b62cd1a7bd6460ee65f6
Processing  'certdata.txt' ...
Done (136 CA certs processed, 24 skipped).
```

#### 2. Filter ca-bundle.crt


Using `make-ca-bundle.py` [^1] to filter `ca-bundle.crt` using the names of the most common Certificate Authorities in `cmn_crt_authorities.csv`.

```console
$ ./make-ca-bundle.py ca-bundle.crt cmn_crt_authorities.csv
```

This will create `ca_bundle_mp.py` file with the selected certificates.


#### 3. Split `ca_bundle_mp.py` into ca-bundles grouped by CA.

Using `make-certifi.py` will split the filtered ca-bundle into installable packages by CA name
.e.g `require("certifi-digicert")`


#### 4. Automate using Makefile

Automate updates to ca-certificates using `$ make certifi`


#### 5. Default ca-bundle.

`certifi` package will include CA Root certs `ISRG Root X1` which is used to validate MicroPython `mip` server and `DigiCert Global Root CA`, which is used to validate `github.com`. This way `mip` can validate by default that the package being installed comes in fact from MicroPython package index server, or from the github repo of a 3rd party package. 


#### 6. Install

In a manifest file:
```python
require("certifi")
# or any additional bundle e.g.
# require("certifi-digicert")
```
Install additional bundles with mip at runtime
```console
>>> import mip
>>> mip.install("certifi-digicert")
```

#### 7. Usage

```console
>>> import certifi
# check config
>>> certifi.config()
{'certs': 'certifi.default', 'path': 'cacerts'}
```
Defaults can be configured, where `certs` can be the module where CA certs are or the CA cert chain as bytes. And `path` is where CA certs files will be loaded from. 
If both options are indicated, then both CA certs will be concatenated into CA cert chain. 


```console
# get default certificates
>>> certifi.load_ca_certs()
b'\nISRG Root X1\n============\n-----BEGIN CERTIFICATE-----\nMIIFazCCA1OgAwIBAgIRAIIQz7DS...'
```

### Notes:

[^1]: This script is adapted from `esp-idf/components/mbedtls/esp_crt_bundle/`
