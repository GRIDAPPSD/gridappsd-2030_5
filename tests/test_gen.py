from pathlib import Path


def test_gen_011(base_config):
    device = base_config["devices"][0]
    key_pth = Path(base_config["tls_repository"]).expanduser().resolve(
        strict=True) / "private" / f"{device}.key"
    cert_pth = Path(base_config["tls_repository"]).expanduser().resolve(
        strict=True) / "certs" / f"{device}.crt"

    assert key_pth
    assert cert_pth
