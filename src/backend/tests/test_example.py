"""示例测试文件，验证测试环境是否正常。"""

import pytest


def test_example():
    """简单的示例测试。"""
    assert 1 + 1 == 2


def test_another_example():
    """另一个示例测试。"""
    assert "hello" in "hello world"


@pytest.mark.unit
def test_unit_marker():
    """使用 unit marker 的测试。"""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """使用 integration marker 的测试。"""
    assert True
