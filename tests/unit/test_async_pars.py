import pytest
from unittest.mock import AsyncMock, patch

from parser.async_pars import get_ref


@pytest.mark.asyncio
async def test_get_ref_success():
    mock_session = AsyncMock()

    test_html = """
    <html>
        <body>
            <a class="accordeon-inner__item-title link xls" href="/file1.xls">File 1</a>
            <a class="accordeon-inner__item-title link xls" href="/file2.xls">File 2</a>
            <a class="other-class" href="/ignore.xls">Ignore</a>
        </body>
    </html>
    """

    with patch('parser.async_pars.parse', return_value=test_html):
        result = await get_ref(1, mock_session)

        assert result == ["/file1.xls", "/file2.xls"]
        assert len(result) == 2


@pytest.mark.asyncio
async def test_get_ref_no_links():
    mock_session = AsyncMock()

    test_html = """
    <html>
        <body>
            <a class="other-class" href="/ignore.xls">Ignore</a>
            <div>No links here</div>
        </body>
    </html>
    """

    with patch('parser.async_pars.parse', return_value=test_html):
        result = await get_ref(1, mock_session)

        assert result == []
        assert len(result) == 0


@pytest.mark.asyncio
async def test_get_ref_different_page():
    mock_session = AsyncMock()

    test_html = """
    <html>
        <body>
            <a class="accordeon-inner__item-title link xls" href="/file3.xls">File 3</a>
        </body>
    </html>
    """

    with patch('parser.async_pars.parse', return_value=test_html):
        result = await get_ref(2, mock_session)

        assert result == ["/file3.xls"]
        assert len(result) == 1


@pytest.mark.asyncio
async def test_parse_headers():
    from parser.async_pars import headers

    assert headers["Accept"] == "text/html"
    assert "User-Agent" in headers
    assert "Mozilla" in headers["User-Agent"]
