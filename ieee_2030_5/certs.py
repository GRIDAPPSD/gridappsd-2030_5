import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from ieee_2030_5.execute import execute_command

__all__ = ['TLSRepository']

from ieee_2030_5.types_ import PathStr, Lfdi
from ieee_2030_5.utils.tls_wrapper import TLSWrap, OpensslWrapper

_log = logging.getLogger(__name__)


def lfdi_from_fingerprint(fingerprint: str) -> Lfdi:
    fp = fingerprint.replace(":", "")
    return Lfdi(fp[:40].encode('ascii'))


def sfdi_from_lfdi(lfdi: Lfdi) -> int:
    assert len(lfdi) == 40, "lfdi must be 160-bits (40 hex characters) long."
    hex_str = str(int(lfdi[:9], 16))
    check_bit = 1
    while not (int(hex_str[-2:]) + check_bit) % 10 == 0:
        check_bit += 1
    return int(hex_str + str(check_bit))


class TLSRepository:

    def __init__(self, repo_dir: PathStr, openssl_cnffile_template: PathStr, serverhost: str, proxyhost: str = None,
                 clear=False):
        if isinstance(repo_dir, str):
            repo_dir = Path(repo_dir).expanduser().resolve()
        if isinstance(openssl_cnffile_template, str):
            openssl_cnffile_template = Path(openssl_cnffile_template).expanduser().resolve()
            if not openssl_cnffile_template.exists():
                raise ValueError(f"openssl_cnffile does not exist {openssl_cnffile_template}")
        self._repo_dir = repo_dir
        self._certs_dir = repo_dir.joinpath("certs")
        self._private_dir = repo_dir.joinpath("private")
        self._combined_dir = repo_dir.joinpath("combined")
        self._openssl_cnf_file = self._repo_dir.joinpath(openssl_cnffile_template.name)
        self._common_names = {serverhost: serverhost}
        if proxyhost:
            self._common_names[proxyhost] = proxyhost
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

        new_contents = openssl_cnffile_template.read_text().replace("dir             = /home/gridappsd/tls",
                                                                    f"dir = {repo_dir}")
        self._openssl_cnf_file.write_text(new_contents)
        self._ca_key = self._private_dir.joinpath("ca.pem")
        self._ca_cert = self._certs_dir.joinpath("ca.crt")
        self._serverhost = serverhost
        self._proxyhost = proxyhost

        self._tls: TLSWrap = OpensslWrapper(self._openssl_cnf_file)
        self._cert_paths: List[Path] = []

        # Create a new ca key if not exists.
        if not Path(self._ca_key).exists():
            self.__create_ca__()
            self._tls.tls_create_private_key(self.__get_key_file__(self._serverhost))
            self.create_cert(self._serverhost, True)
            if proxyhost:
                self.create_cert(self._proxyhost, True)

        if not clear:
            for f in self._certs_dir.glob('*.crt'):
                f = Path(f)
                self._cert_paths.append(f)
                cn = self.get_common_name(f.stem)
                if cn not in ('ca', serverhost):
                    self._client_common_name_set.add(cn)

    def __create_ca__(self):
        self._tls.tls_create_private_key(self._ca_key)
        self._tls.tls_create_ca_certificate("ca", self._ca_key, self._ca_cert)
        self._tls.tls_create_pkcs23_pem_and_cert(self._ca_key, self._ca_cert, self.__get_combined_file__("ca"))

    def create_cert(self, common_name: str, as_server: bool = False):

        if not self.__get_key_file__(common_name).exists():
            self._tls.tls_create_private_key(self.__get_key_file__(common_name))

        self._tls.tls_create_signed_certificate(common_name, self._ca_key,
                                                self._ca_cert, self.__get_key_file__(common_name),
                                                self.__get_cert_file__(common_name), as_server)

        self._tls.tls_create_pkcs23_pem_and_cert(self.__get_key_file__(common_name),
                                                 self.__get_cert_file__(common_name),
                                                 self.__get_combined_file__(common_name))

        self._common_names[common_name] = common_name

    def lfdi(self, device_id: str) -> Lfdi:
        """
        Using the fingerprint of the certifcate return the left truncation of 160 bits with no check digit.
        Example:
          From:
            3E4F-45AB-31ED-FE5B-67E3-43E5-E456-2E31-984E-23E5-349E-2AD7-4567-2ED1-45EE-213A
          Return:
            3E4F-45AB-31ED-FE5B-67E3-43E5-E456-2E31-984E-23E5
            as an integer.
        """
        # 160 / 4 == 40
        fp = self.fingerprint(device_id, True)
        return lfdi_from_fingerprint(fp)

    def sfdi_from_lfdi(self, lfdi: Lfdi) -> int:
        print(len(lfdi))
        assert len(lfdi) == 40, "lfdi must be 160-bits (40 hex characters) long."
        hex_str = str(int(lfdi[:9], 16))
        check_bit = 1
        while not (int(hex_str[-2:]) + check_bit) % 10 == 0:
            check_bit += 1
        return int(hex_str + str(check_bit))

    def sfdi(self, device_id: str):
        lfdi_ = self.lfdi(device_id)
        return self.sfdi_from_lfdi(lfdi_)

    def fingerprint(self, device_id: str, without_colan: bool = True) -> str:
        value = self._tls.tls_get_fingerprint_from_cert(self.__get_cert_file__(device_id))
        if without_colan:
            value = value.replace(":", "")
        if "=" in value:
            value = value.split("=")[1]
        return value

    def get_common_name(self, device_id: str) -> x509:
        pem_data = Path(self.__get_cert_file__(device_id)).read_bytes()
        cert = x509.load_pem_x509_certificate(pem_data, default_backend())
        return cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value

    def get_file_pair(self, device_id: str) -> Tuple[str, str]:
        """ Get cert, key from the repository based on passed device_id"""
        return (self.__get_cert_file__(device_id).as_posix(),
                self.__get_key_file__(device_id).as_posix())

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
    def proxy_key_file(self) -> Path:
        if not self._proxyhost:
            raise ValueError("No proxy host available")
        return self.__get_key_file__(self._proxyhost)

    @property
    def proxy_cert_file(self) -> Path:
        if not self._proxyhost:
            raise ValueError("No proxy host available")
        return self.__get_cert_file__(self._proxyhost)

    @property
    def server_key_file(self) -> Path:
        return self.__get_key_file__(self._serverhost)

    @property
    def server_cert_file(self) -> Path:
        return self.__get_cert_file__(self._serverhost)

    def find_device_id_from_sfdi(self, sfdi: int) -> Optional[str]:
        """
        Searches the certificate paths for a device id that maps to the sfdi passed into the method.
        Args:
            sfdi:

        Returns:

        """
        device_id = None
        for d in self._cert_paths:
            if sfdi == self.sfdi(d.stem):
                device_id = d.stem
                break
        return device_id

    def __get_cert_file__(self, common_name: str) -> Path:
        return self._certs_dir.joinpath(f"{common_name}.crt")

    def __get_key_file__(self, common_name: str) -> Path:
        return self._private_dir.joinpath(f"{common_name}.pem")

    def __get_combined_file__(self, common_name: str) -> Path:
        return self._combined_dir.joinpath(f"{common_name}-combined.pem")


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", help="Directory of certificates determine lfdi and sfdi from.")
    parser.add_argument("--file", help="File to determine lfdi and sfdi from.")

    opts = parser.parse_args()

    if opts.dir and opts.file:
        sys.stderr.write("Only specify dir or file.\n")
        sys.exit(1)
    elif opts.dir is None and opts.file is None:
        sys.stderr.write("Must specify either --dir or --file.\n")
        sys.exit(1)

    target = opts.file
    if opts.dir:
        target = opts.dir

    target = Path(target)
    if not target.exists():
        sys.stderr.write("Invalid file or directory refrence.\n")
        sys.exit(1)

    if target.is_dir():
        targets = [target.glob("*.crt")]
    else:
        targets = [target]

    for t in targets:
        fingerprint = OpensslWrapper.tls_get_fingerprint_from_cert(t)
        lfdi = lfdi_from_fingerprint(fingerprint)
        sfdi = sfdi_from_lfdi(lfdi)
        sys.stdout.write(f"certificate: {t}\n")
        sys.stdout.write(f"-" * 60 + "\n")
        sys.stdout.write(f"fingerprint: {fingerprint}\n")
        sys.stdout.write(f"lfdi: {lfdi.decode('ascii')}\n")
        sys.stdout.write(f"sfdi: {sfdi}\n\n")


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    fingerprint = "3E4F-45AB-31ED-FE5B-67E3-43E5-E456-2E31-984E-23E5-349E-2AD7-4567-2ED1-45EE-213A".replace("-", "")
    lfdi = lfdi_from_fingerprint(fingerprint)
    sfdi = sfdi_from_lfdi(lfdi)
    print(f"fingerprint: {fingerprint}")
    print(f"lfdi: {lfdi}")
    print(f"sfdi: {sfdi}")
    #
    # tlsrepo = TLSRepository(repo_dir="~/tls",
    #                         openssl_cnffile_template="../openssl.cnf",
    #                         clear=False,
    #                         serverhost="gridappsd_dev_2004:8443")
    # fingerprint = tlsrepo.fingerprint("dev1")
    # # fingerprint = "3F4F-45AB-31ED-FE5B-67E3-43E5-E456-2E31-984E-23E5-349E-2AD7-4567-2ED1-45EE-213B".replace("-", "")
    # print(len(fingerprint))
    # print("my lfdi: ", fingerprint[:40])
    # tlsrepo.sfdi_from_lfdi(fingerprint[:40].encode("ascii"))
    # # Each char is 4 bits so 9*4 == 36
    # print("left 36 bits: ", fingerprint[:9])
    # print("to int from fingerprint", int(fingerprint[:9], 16))
    # interum = str(int(fingerprint[:9], 16))
    # print(int(interum[-2:]))
    # add_value = 1
    # while not (int(interum[-2:]) + add_value) % 10 == 0:
    #     add_value += 1
    #
    # print(add_value)
    # interum = interum + str(add_value)
    # print(f"sfdi = ", interum)
    #
    # print(f" our sfdi: {tlsrepo.sfdi('dev1')}")
    #
    # _log.debug(f"fingerprint: {tlsrepo.fingerprint('dev1', False)}")
    #
    # _log.debug(f"dev1 lfdi: {tlsrepo.lfdi('dev1')}, sfdi: {tlsrepo.sfdi('dev1')}")
