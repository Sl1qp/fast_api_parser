import pytest
from parser.parser import run_parser, parse_table


@pytest.mark.asyncio
async def test_run_parser_success(mocker):
    mock_get_urls = mocker.patch('parser.parser.get_tables_urls')
    mock_download = mocker.patch('parser.parser.download_xls')
    mock_parse = mocker.patch('parser.parser.parse_table')

    mock_get_urls.return_value = ['url1', 'url2']
    mock_download.return_value = 'test_file.xls'
    mock_parse.return_value = True

    await run_parser(stopper_threshold=15, max_pages=1)

    assert mock_get_urls.call_count == 1
    assert mock_download.call_count == 2
    assert mock_parse.call_count == 2


@pytest.mark.asyncio
async def test_run_parser_stop_condition(mocker):
    mock_get_urls = mocker.patch('parser.parser.get_tables_urls')
    mock_download = mocker.patch('parser.parser.download_xls')
    mock_parse = mocker.patch('parser.parser.parse_table')

    mock_get_urls.return_value = ['url1']
    mock_download.return_value = 'test_file.xls'
    mock_parse.return_value = False

    await run_parser(stopper_threshold=3)

    assert mock_get_urls.call_count == 3
    assert mock_download.call_count == 3
    assert mock_parse.call_count == 3


@pytest.mark.asyncio
async def test_parse_table_skip_old_file(mocker):
    mock_read_excel = mocker.patch('parser.parser.pd.read_excel')
    mock_save = mocker.patch('parser.parser.create_and_save_data')
    mock_remove = mocker.patch('parser.parser.os.remove')

    result = await parse_table('trades_file\oil_xls_20201204162000.xls')

    assert result is False
    mock_read_excel.assert_not_called()
    mock_save.assert_not_called()
    mock_remove.assert_called_once_with('trades_file\oil_xls_20201204162000.xls')
