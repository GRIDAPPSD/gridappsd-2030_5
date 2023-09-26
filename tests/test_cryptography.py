from ieee_2030_5.utils import CryptographyWrapper
from pathlib import Path

def test_create_pk():
    pth = Path("testing/pk/abc.pem")
    wrapper = CryptographyWrapper()
    assert wrapper.tls_create_private_key(pth)
    assert Path(pth).exists()
    pem_key = Path(pth).read_bytes().decode()
    assert "BEGIN PRIVATE KEY" in pem_key
    assert "END PRIVATE KEY" in pem_key
    pth.unlink()

def test_create_ca():
    try:
        pth = Path("testing/ca.pem")
        crt_pth = Path("testing/ca.crt")
        wrapper = CryptographyWrapper()
        wrapper.tls_create_ca_certificate("myca", pth, crt_pth)
        assert pth.exists()
        assert crt_pth.exists()
    finally:
        pth.unlink(missing_ok=True)
        crt_pth.unlink(missing_ok=True)