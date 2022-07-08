import logging
from pathlib import Path
from typing import List

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from ieee_2030_5.execute import execute_command

__all__ = ['TLSRepository']

from ieee_2030_5.types import PathStr, Lfid

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
        self._combined_dir = repo_dir.joinpath("combined")
        self._openssl_cnf_file = self._repo_dir.joinpath(openssl_cnffile.name)
        self._common_names = {serverhost: serverhost}
        self._client_common_name_set = set()

        if not self._repo_dir.exists() or not self._certs_dir.exists() or \
                not self._private_dir.exists() or not self._combined_dir.exists():
            self._certs_dir.mkdir(parents=True)
            self._private_dir.mkdir(parents=True)
            self._combined_dir.mkdir(parents=True)

        index_txt = self._repo_dir.joinpath("index.txt")
        serial = self._repo_dir.joinpath("serial")
        if clear:
            for x in self._private_dir.iterdir():
                x.unlink()
            for x in self._certs_dir.iterdir():
                x.unlink()
            for x in self._combined_dir.iterdir():
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

        new_contents = openssl_cnffile.read_text().replace("dir             = /home/gridappsd/tls",
                                                           f"dir = {repo_dir}")
        self._openssl_cnf_file.write_text(new_contents)
        self._ca_key = self._private_dir.joinpath("ca.pem")
        self._ca_cert = self._certs_dir.joinpath("ca.crt")
        self._serverhost = serverhost

        # Create a new ca key if not exists.
        if not Path(self._ca_key).exists():
            self.__create_ca__()
            __openssl_create_private_key__(self.__get_key_file__(self._serverhost))
            self.create_cert(self._serverhost, True)

        if not clear:
            for f in self._certs_dir.glob('*.crt'):
                f = Path(f)
                cn = self.get_common_name(f.stem)
                if cn not in ('ca', serverhost):
                    self._client_common_name_set.add(cn)

    def __create_ca__(self):
        __openssl_create_private_key__(self._ca_key)
        __openssl_create_ca_certificate__("ca", self._openssl_cnf_file, self._ca_key,
                                          self._ca_cert)

    def create_cert(self, common_name: str, as_server: bool = False):
        if not self.__get_key_file__(common_name).exists():
            __openssl_create_private_key__(self.__get_key_file__(common_name))
        __openssl_create_signed_certificate__(common_name, self._openssl_cnf_file, self._ca_key,
                                              self._ca_cert, self.__get_key_file__(common_name),
                                              self.__get_cert_file__(common_name), as_server)

        __openssl_create_pkcs23_pem_and_cert__(self.__get_key_file__(common_name), self.__get_cert_file__(common_name),
                                               self.__get_combined_file__(common_name))

        self._common_names[common_name] = common_name

    def lfdi(self, device_id: str) -> Lfid:
        fp = self.fingerprint(device_id, True)
        return Lfid(int(fp[:16], 16))

    def sfdi(self, device_id: str):
        lfdi_: int = self.lfdi(device_id)
        bit_left_truncation_len = 36
        # truncate the lFDI
        sfdi_no_sod_checksum = lfdi_ >> (lfdi_.bit_length() - bit_left_truncation_len)
        # calculate sum-of-digits checksum digit
        sod_checksum = 10 - sum([int(digit) for digit in str(sfdi_no_sod_checksum)]) % 10
        # right concatenate the checksum digit and return
        return str(sfdi_no_sod_checksum) + str(sod_checksum)

    def fingerprint(self, device_id: str, without_colan: bool = True) -> str:
        value = __openssl_fingerprint__(self.__get_cert_file__(device_id))
        if without_colan:
            value = value.replace(":", "")
        if "=" in value:
            value = value.split("=")[1]
        return value

    def get_common_name(self, device_id: str) -> x509:
        pem_data = Path(self.__get_cert_file__(device_id)).read_bytes()
        cert = x509.load_pem_x509_certificate(pem_data, default_backend())
        return cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value

    @property
    def client_list(self) -> List[str]:
        return list(self._client_common_name_set)

    @property
    def ca_key_file(self) -> Path:
        return self._ca_key

    @property
    def ca_cert_file(self) -> Path:
        return self._ca_cert

    @property
    def server_key_file(self) -> Path:
        return self.__get_key_file__(self._serverhost)

    @property
    def server_cert_file(self) -> Path:
        return self.__get_cert_file__(self._serverhost)

    def __get_cert_file__(self, common_name: str) -> Path:
        return self._certs_dir.joinpath(f"{common_name}.crt")

    def __get_key_file__(self, common_name: str) -> Path:
        return self._private_dir.joinpath(f"{common_name}.pem")

    def __get_combined_file__(self, common_name: str) -> Path:
        return self._combined_dir.joinpath(f"{common_name}-combined.pem")


def __openssl_create_pkcs23_pem_and_cert__(private_key_file: Path, cert_file: Path, combined_file: Path):
    # openssl pkcs12 -export -in certificate.pem -inkey privatekey.pem -out cert-and-key.pfx
    tmpfile = Path("/tmp/tmp.p12")
    tmpfile2 = Path("/tmp/all.pem")
    tmpfile.unlink(missing_ok=True)
    cmd = ["openssl", "pkcs12", "-export", "-in", str(cert_file), "-inkey", str(private_key_file), "-out", str(tmpfile), "-passout", "pass:"]
    execute_command(cmd)

    # openssl pkcs12 -in path.p12 -out newfile.pem -nodes
    cmd = ["openssl", "pkcs12", "-in", str(tmpfile), "-out", str(tmpfile2), "-nodes", "-passin", "pass:"]
    #cmd = ["openssl", "pkcs12", "-in", str(tmpfile), "-out", str(combined_file), "-clcerts", "-nokeys", "-passin", "pass:"]
    # -clcerts -nokeys
    execute_command(cmd)

    with open(combined_file, "w") as fp:
        in_between = False
        for line in tmpfile2.read_text().split("\n"):
            if not in_between:
                if "BEGIN" in line:
                    fp.write(f"{line}\n")
                    in_between = True
            else:
                fp.write(f"{line}\n")
                if "END" in line:
                    in_between = False


def __openssl_create_private_key__(file_path: Path):
    # openssl ecparam -out private/ec-cakey.pem -name prime256v1 -genkey
    cmd = ["openssl", "ecparam", "-out", str(file_path), "-name", "prime256v1", "-genkey"]
    return execute_command(cmd)


def __openssl_create_ca_certificate__(common_name: str, opensslcnf: Path, private_key_file: Path,
                                      ca_cert_file: Path):
    # openssl req -new -x509 -days 3650 -config openssl.cnf \
    #   -extensions v3_ca -key private/ec-cakey.pem -out certs/ec-cacert.pem
    cmd = [
        "openssl", "req", "-new", "-x509", "-days", "3650", "-subj", f"/C=US/CN={common_name}",
        "-config",
        str(opensslcnf), "-extensions", "v3_ca", "-key",
        str(private_key_file), "-out",
        str(ca_cert_file)
    ]
    return execute_command(cmd)


def __openssl_create_csr__(common_name: str, opensslcnf: Path, private_key_file: Path,
                           server_csr_file: Path):
    # openssl req -new -key server.key -out server.csr -sha256
    cmd = [
        "openssl", "req", "-new", "-config",
        str(opensslcnf), "-subj", f"/C=US/CN={common_name}", "-key",
        str(private_key_file), "-out",
        str(server_csr_file), "-sha256"
    ]
    return execute_command(cmd)


def __openssl_create_signed_certificate__(common_name: str,
                                          opensslcnf: Path,
                                          ca_key_file: Path,
                                          ca_cert_file: Path,
                                          private_key_file: Path,
                                          cert_file: Path,
                                          as_server: bool = False):
    csr_file = Path(f"/tmp/{common_name}")
    __openssl_create_csr__(common_name, opensslcnf, private_key_file, csr_file)
    # openssl ca -keyfile /root/tls/private/ec-cakey.pem -cert /root/tls/certs/ec-cacert.pem \
    #   -in server.csr -out server.crt -config /root/tls/openssl.cnf
    cmd = [
        "openssl",
        "ca",
        "-keyfile",
        str(ca_key_file),
        "-cert",
        str(ca_cert_file),
        "-subj",
        f"/C=US/CN={common_name}",
        "-in",
        str(csr_file),
        "-out",
        str(cert_file),
        "-config",
        str(opensslcnf),
    # For no prompt use -batch
        "-batch"
    ]
    # if as_server:
    #     "-server"
    # print(" ".join(cmd))
    ret_value = execute_command(cmd)
    csr_file.unlink()
    return ret_value


def __openssl_fingerprint__(cert_file: Path, algorithm: str = "sha1"):

    if algorithm == "sha1":
        algorithm = "-sha1"
    else:
        raise NotImplementedError()

    cmd = ["openssl", "x509", "-in", str(cert_file), "-noout", "-fingerprint", algorithm]
    ret_value = execute_command(cmd)
    return ret_value
