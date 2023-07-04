import ussl as _ssl
from ussl import (
    CERT_NONE,
    CERT_REQUIRED,
    CERT_OPTIONAL,
    PROTOCOL_TLS_CLIENT,
    PROTOCOL_TLS_SERVER,  # noqa
    wrap_socket,  # noqa
    MBEDTLS_VERSION,  # noqa
)


class SSLContext:
    def __init__(self, protocol):
        # protocol is PROTOCOL_TLS_CLIENT or PROTOCOL_TLS_SERVER
        self._protocol = protocol
        self._check_hostname = False

        self.ctx = _ssl.SSLContext(self._protocol)
        if protocol == PROTOCOL_TLS_CLIENT:
            self.ctx.verify_mode = CERT_REQUIRED
            self.check_hostname = True
        self.cadata = None

    @property
    def protocol(self):
        return self._protocol

    @property
    def check_hostname(self):
        return self._check_hostname

    @check_hostname.setter
    def check_hostname(self, value):
        assert type(value) == bool

        if value is True and not self.ctx.verify_mode:
            self.ctx.verify_mode = CERT_REQUIRED

        self._check_hostname = value

    @property
    def verify_mode(self):
        return self.ctx.verify_mode

    @verify_mode.setter
    def verify_mode(self, value):
        assert value in (CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED)
        if not self.check_hostname:
            self.ctx.verify_mode = value

    def load_cert_chain(self, certfile, keyfile=None):
        if isinstance(certfile, bytes):
            pass
        else:
            with open(certfile, "rb") as cert:
                certfile = cert.read()
        if keyfile:
            if isinstance(keyfile, bytes):
                pass
            else:
                with open(keyfile, "rb") as key:
                    keyfile = key.read()

        self.ctx.load_cert_chain(certfile, keyfile=keyfile)

    def load_default_certs(self):
        pass

    def load_verify_locations(self, cafile=None, capath=None, cadata=None):
        if cafile:
            with open(cafile, "rb") as ca_cert:
                cadata = ca_cert.read()
        if capath:
            pass  ## not implemented, it needs to concatenate multiple files

        # if cadata:
        #     self.cadata = True

        self.ctx.load_verify_locations(cadata=cadata)

    def get_ciphers(self):
        return self.ctx.get_ciphers()

    def set_ciphers(self, ciphersuite):
        ciphersuite = ciphersuite.split(":")
        self.ctx.set_ciphers(ciphersuite)

    def wrap_socket(  # noqa
        self,
        sock,
        server_side=False,
        do_handshake_on_connect=True,
        server_hostname=None,
    ):
        if self.check_hostname and server_hostname is None:
            raise ValueError("check_hostname requires server_hostname")

        return self.ctx.wrap_socket(
            sock,
            server_side=server_side,
            server_hostname=server_hostname,
            do_handshake_on_connect=do_handshake_on_connect,
        )
