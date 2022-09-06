from typing import Optional

import pytest


def test_basic_001():
    pytest.skip("DNS lookup not supported!")


def test_basic_002(first_client):
    dcap = first_client.device_capability()
    assert dcap.href
    assert dcap.pollRate
    tm = first_client.time()
    assert tm.localTime
    assert tm.tzOffset
    assert tm.dstEndTime
    assert tm.currentTime
    assert tm.dstOffset


def test_basic_003():
    raise NotImplementedError()


def test_basic_004():
    raise NotImplementedError()


def test_basic_005():
    raise NotImplementedError()


def test_basic_006():
    raise NotImplementedError()


def test_basic_007():
    raise NotImplementedError()


def test_basic_008():
    raise NotImplementedError()


def test_basic_009():
    raise NotImplementedError()


def test_basic_010():
    raise NotImplementedError()


def test_basic_011():
    raise NotImplementedError()


def test_basic_012():
    raise NotImplementedError()


def test_basic_013():
    raise NotImplementedError()


def test_basic_014():
    raise NotImplementedError()


def test_basic_015():
    raise NotImplementedError()


def test_basic_016():
    raise NotImplementedError()


def test_basic_017():
    raise NotImplementedError()


def test_basic_018():
    raise NotImplementedError()


def test_basic_019():
    raise NotImplementedError()


def test_basic_020():
    raise NotImplementedError()


def test_basic_021():
    raise NotImplementedError()


def test_basic_022():
    raise NotImplementedError()


def test_basic_023():
    raise NotImplementedError()


def test_basic_024():
    raise NotImplementedError()


def test_basic_025():
    raise NotImplementedError()


def test_basic_026():
    raise NotImplementedError()


def test_basic_027():
    raise NotImplementedError()


def test_basic_028():
    raise NotImplementedError()


def test_basic_029():
    raise NotImplementedError()
