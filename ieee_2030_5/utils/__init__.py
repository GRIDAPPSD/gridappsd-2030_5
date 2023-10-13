import base64
import uuid
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional, Type

from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.parsers.xml import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from ieee_2030_5.models.sep import EndDevice, EndDeviceList

__xml_context__ = XmlContext()
__parser_config__ = ParserConfig(fail_on_unknown_attributes=True, fail_on_unknown_properties=True)
__xml_parser__ = XmlParser(config=__parser_config__,
                           context=__xml_context__,
                           handler=LxmlEventHandler)
__config__ = SerializerConfig(xml_declaration=False, pretty_print=True)
__serializer__ = XmlSerializer(config=__config__)
__ns_map__ = {None: "urn:ieee:std:2030.5:ns"}

import ieee_2030_5.types_ as t
import ieee_2030_5.utils as tls


class PrivateKeyDeosntExist(Exception):

    def __init__(self, private_key_path: Path):
        super().__init__()
        self.pk_path = private_key_path

    def __str__(self) -> str:
        return f"The path {self.pk_path} does not exist!"


class CertExistsError(Exception):

    def __init__(self, cert_path: Path):
        super().__init__()
        self.cert_path = cert_path

    def __str__(self) -> str:
        return f"The path {self.cert_path} already exists!"


class CADoesNotExist(Exception):

    def __str__(self) -> str:
        return "The CA certificate does not exist!"


def serialize_dataclass(obj: dataclass) -> str:
    """
    Serializes a dataclass that was created via xsdata to an xml string for
    returning to a client.
    """
    return __serializer__.render(obj, ns_map=__ns_map__)


def xml_to_dataclass(xml: str, type: Optional[Type] = None) -> dataclass:
    """
    Parse the xml passed and return result from loaded classes.
    """
    parsed = __xml_parser__.from_string(xml, type)

    # The xml parser from string seems to double decode the lfDI which
    # probably means I am doing something wrong.  However, this fixes
    # the issue and it is correct after we encode the lFDI.  I will
    # do the same with other entities as needed.
    if isinstance(parsed, EndDevice) and parsed.lFDI:
        parsed.lFDI = base64.b16encode(parsed.lFDI)
    elif isinstance(parsed, EndDeviceList):
        for ed in parsed.EndDevice:
            if ed.lFDI:
                ed.lFDI = base64.b16encode(ed.lFDI)

    return parsed


def dataclass_to_xml(dc: dataclass) -> str:
    return serialize_dataclass(dc)


def get_lfdi_from_cert(path: Path) -> t.Lfdi:
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
    fp = tls.OpensslWrapper.tls_get_fingerprint_from_cert(path)
    fp = fp.replace(":", "")
    lfdi = t.Lfdi(fp[:40])
    return lfdi


def get_sfdi_from_lfdi(lfdi: t.Lfdi) -> int:
    """

    Args:
        lfdi:

    Returns:

    """
    from ieee_2030_5.certs import sfdi_from_lfdi
    return sfdi_from_lfdi(lfdi)


def uuid_2030_5() -> str:
    return str(uuid.uuid4()).replace('-', '').upper()


class TLSWrap:

    @staticmethod
    def tls_create_private_key(file_path: Path):
        """
        Creates a private key in the path that is specified.  The path will be overwritten
        if it already exists.

        Args:
            file_path:

        Returns:

        """
        raise NotImplementedError()

    @staticmethod
    def tls_create_ca_certificate(common_name: str, private_key_file: Path, ca_cert_file: Path):
        """
        Create a ca certificate from using common name private key and ca certificate file.

        Args:
            common_name:
            private_key_file:
            ca_cert_file:

        Returns:

        """
        raise NotImplementedError()

    @staticmethod
    def tls_create_csr(common_name: str, private_key_file: Path, server_csr_file: Path):
        """

        Args:
            common_name:
            private_key_file:
            server_csr_file:

        Returns:

        """
        raise NotImplementedError()

    @staticmethod
    def tls_create_signed_certificate(common_name: str,
                                      ca_key_file: Path,
                                      ca_cert_file: Path,
                                      private_key_file: Path,
                                      cert_file: Path,
                                      as_server: bool = False):
        """

        Args:
            common_name:
            ca_key_file:
            ca_cert_file:
            private_key_file:
            cert_file:
            as_server:

        Returns:

        """
        raise NotImplementedError()

    @staticmethod
    def tls_get_fingerprint_from_cert(cert_file: Path, algorithm: str = "sha256") -> str:
        """

        Args:
            cert_file:
            algorithm:

        Returns:

        """

    @staticmethod
    def tls_create_pkcs23_pem_and_cert(private_key_file: Path, cert_file: Path,
                                       combined_file: Path):
        """

        Args:
            private_key_file:
            cert_file:
            combined_file:

        Returns:

        """
        raise NotImplementedError()


from ieee_2030_5.utils.tls_wrapper import OpensslWrapper
from ieee_2030_5.utils.cryptography_wrapper import CryptographyWrapper

__all__ = ['OpensslWrapper', 'CryptographyWrapper']
