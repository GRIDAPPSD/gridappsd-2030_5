import logging
from pathlib import Path

from IEEE2030_5 import PathStr
from IEEE2030_5.execute import execute_command


__all__ = ['TLSRepository']

_log = logging.getLogger(__name__)


class TLSRepository:

    def __init__(self, repo_dir: PathStr, openssl_cnffile: PathStr, serverhost: str, clear=False):
        if isinstance(repo_dir, str):
            repo_dir = Path(repo_dir).expanduser().resolve()
        if isinstance(openssl_cnffile, str):
            openssl_cnffile = Path(openssl_cnffile).expanduser().resolve()
            if not openssl_cnffile.exists():
                raise ValueError(f"openssl_cnffile does not exist {openssl_cnffile}")
        self._repo_dir = repo_dir
        self._certs_dir = repo_dir.joinpath("certs")
        self._private_dir = repo_dir.joinpath("private")
        self._openssl_cnf_file = self._repo_dir.joinpath(openssl_cnffile.name)

        if not self._repo_dir.exists():
            self._certs_dir.mkdir(parents=True)
            self._private_dir.mkdir(parents=True)

        index_txt = self._repo_dir.joinpath("index.txt")
        serial = self._repo_dir.joinpath("serial")
        if clear:
            for x in self._private_dir.iterdir():
                x.unlink()
            for x in self._certs_dir.iterdir():
                x.unlink()
            for x in self._repo_dir.iterdir():
                if x.is_file():
                    x.unlink()
            try:
                index_txt.unlink()
            except FileNotFoundError:
                pass
            try:
                serial.unlink()
            except FileNotFoundError:
                pass

        if not index_txt.exists():
            index_txt.write_text("")
        if not serial.exists():
            serial.write_text("01")

        self._openssl_cnf_file.write_text(openssl_cnffile.read_text())
        self._ca_key = self._private_dir.joinpath("ca.pem")
        self._ca_cert = self._certs_dir.joinpath("ca.crt")
        self._serverhost = serverhost

        self.__create_ca__()
        _openssl_create_private_key(self.__get_key_file__(self._serverhost))
        self.create_cert(self._serverhost, True)

    def __create_ca__(self):
        _openssl_create_private_key(self._ca_key)
        _openssl_create_ca_certificate("ca", self._openssl_cnf_file, self._ca_key, self._ca_cert)

    def create_cert(self, hostname: str, as_server: bool = False):
        if not self.__get_key_file__(hostname).exists():
            _openssl_create_private_key(self.__get_key_file__(hostname))
        _openssl_create_signed_certificate(hostname, self._openssl_cnf_file, self._ca_key, self._ca_cert,
                                           self.__get_key_file__(hostname), self.__get_cert_file__(hostname),
                                           as_server)

    @property
    def ca_key_file(self) -> Path:
        return self.__get_key_file__(self._serverhost)

    @property
    def ca_cert_file(self) -> Path:
        return self.__get_cert_file__(self._serverhost)

    def __get_cert_file__(self, hostname: str) -> Path:
        return self._certs_dir.joinpath(f"{hostname}.crt")

    def __get_key_file__(self, hostname: str) -> Path:
        return self._private_dir.joinpath(f"{hostname}.pem")


def _openssl_create_private_key(file_path: Path):
    # openssl ecparam -out private/ec-cakey.pem -name prime256v1 -genkey
    cmd = ["openssl", "ecparam", "-out", str(file_path), "-name", "prime256v1", "-genkey"]
    return execute_command(cmd)


def _openssl_create_ca_certificate(common_name: str, opensslcnf: Path, private_key_file: Path, ca_cert_file: Path):
    # openssl req -new -x509 -days 3650 -config openssl.cnf \
    #   -extensions v3_ca -key private/ec-cakey.pem -out certs/ec-cacert.pem
    cmd = ["openssl", "req", "-new", "-x509",
           "-days", "3650",
           "-subj", f"/C=US/CN={common_name}",
           "-config", str(opensslcnf),
           "-extensions", "v3_ca",
           "-key", str(private_key_file),
           "-out", str(ca_cert_file)]
    return execute_command(cmd)


def _openssl_create_csr(common_name: str, opensslcnf:Path, private_key_file: Path, server_csr_file: Path):
    # openssl req -new -key server.key -out server.csr -sha256
    cmd = ["openssl", "req", "-new",
           "-config", str(opensslcnf),
           "-subj", f"/C=US/CN={common_name}",
           "-key", str(private_key_file),
           "-out", str(server_csr_file),
           "-sha256"]
    return execute_command(cmd)


def _openssl_create_signed_certificate(common_name: str, opensslcnf: Path, ca_key_file: Path, ca_cert_file: Path,
                                       private_key_file: Path, cert_file: Path, as_server: bool = False):
    csr_file = Path(f"/tmp/{common_name}")
    _openssl_create_csr(common_name, opensslcnf, private_key_file, csr_file)
    # openssl ca -keyfile /root/tls/private/ec-cakey.pem -cert /root/tls/certs/ec-cacert.pem \
    #   -in server.csr -out server.crt -config /root/tls/openssl.cnf
    cmd = ["openssl", "ca",
           "-keyfile", str(ca_key_file),
           "-cert", str(ca_cert_file),
           "-subj", f"/C=US/CN={common_name}",
           "-in", str(csr_file),
           "-out", str(cert_file),
           "-config", str(opensslcnf),
           # For no prompt use -batch
           "-batch"]
    # if as_server:
    #     "-server"
    # print(" ".join(cmd))
    ret_value = execute_command(cmd)
    csr_file.unlink()
    return ret_value
