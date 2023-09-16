from pathlib import Path

from ieee_2030_5.utils import TLSWrap

class CryptographyWrapper(TLSWrap):
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
    def tls_get_fingerprint_from_cert(cert_file: Path, algorithm: str = "sha256"):
        """

        Args:
            cert_file:
            algorithm:

        Returns:

        """
        raise NotImplementedError()

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