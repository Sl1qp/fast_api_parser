import asyncio
import datetime
import aiohttp
import os
import aiofiles
import database as db
import pandas as pd

from .async_pars import get_ref
from urllib.parse import urlparse

folder_path = "trades_file"

exclude_patterns = [
    "Итого",
    "Секция Биржи: «Нефтепродукты» АО «СПбМТСБ»",
    "Единица измерения: Метрическая тонна",
    "Итого по секции"
]

columns_mapping = {
    'Код\nИнструмента': 'exchange_product_id',
    'Наименование\nИнструмента': 'delivery_product_name',
    'Базис\nпоставки': 'delivery_basis_name',
    'Объем\nДоговоров\nв единицах\nизмерения': 'volume',
    'Обьем\nДоговоров,\nруб.': 'total',
    'Количество\nДоговоров,\nшт.': 'count'
}


async def download_xls(url: str) -> str:
    os.makedirs(folder_path, exist_ok=True)

    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path) or "downloaded_file.xls"
    file_path = os.path.join(folder_path, file_name)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()  # Проверка на ошибки HTTP
            async with aiofiles.open(file_path, "wb") as f:
                while True:
                    chunk = await response.content.read(8192)
                    if not chunk:
                        break
                    await f.write(chunk)

    print(f"[  parser  ] The file {file_path[12:]} downloaded successfully!")
    return file_path


async def get_tables_urls(page: int) -> list:
    trade_ref = []
    async with aiohttp.ClientSession() as session:
        ref = await get_ref(page, session)
        for date in ref:
            trade_ref.append(date)

    return trade_ref


async def parse_table(table_name):
    if int(table_name[20:24]) <= 2023:
        os.remove(table_name)
        return False

    date = f"{table_name[26:28]}.{table_name[24:26]}.{table_name[20:24]}"
    trade_date = datetime.datetime.strptime(date, "%d.%m.%Y")

    try:
        td = pd.read_excel(table_name, engine="xlrd", skiprows=6, header=None)

        header_row = None
        for i, row in td.iterrows():
            if any("Код\nИнструмента" in str(cell) for cell in row):
                header_row = i
                break

        if header_row is not None:
            td.columns = td.iloc[header_row]
            td = td.iloc[header_row + 1:]
        else:
            print(f"Заголовки не найдены в файле {table_name}")
            raise Exception

        for column, new_column in columns_mapping.items():
            if new_column in ["volume", "total", "count"]:
                td[column] = td[column].replace('-', '0', regex=True)
                td[column] = pd.to_numeric(td[column], errors='coerce')
            else:
                td[column] = td[column].astype(str).str.strip()
        os.remove(table_name)
    except Exception as e:
        print(str(e))
        print(f"Ошибка при считывании файла - {table_name}")
        os.remove(table_name)
        return False

    filtered_td = td[td['Количество\nДоговоров,\nшт.'] > 0]

    async with db.async_session_maker() as session:
        await create_and_save_data(session, filtered_td, trade_date, table_name)


async def create_and_save_data(session, filtered_td, trade_date, table_name):
    objects = []
    for index, row in filtered_td.iterrows():
        if row['Код\nИнструмента'].startswith("Итого") or row['Код\nИнструмента'] == "nan":
            continue
        exchange_product_id = row['Код\nИнструмента']
        exchange_product_name = row['Наименование\nИнструмента']
        delivery_basis_name = row['Базис\nпоставки']
        volume = row['Объем\nДоговоров\nв единицах\nизмерения']
        total = row['Обьем\nДоговоров,\nруб.']
        count = row['Количество\nДоговоров,\nшт.']

        trade_obj = db.spimex_trading_results(
            exchange_product_id=exchange_product_id,
            exchange_product_name=exchange_product_name,
            oil_id=exchange_product_id[:4],
            delivery_basis_id=exchange_product_id[4:7],
            delivery_basis_name=delivery_basis_name,
            delivery_type_id=exchange_product_id[-1],
            volume=float(volume),
            total=int(total),
            count=int(count),
            date=trade_date,
            created_on=datetime.datetime.now(),
            updated_on=datetime.datetime.now()
        )
        objects.append(trade_obj)

    if objects:
        session.add_all(objects)
        await session.commit()
    print(f'[ database ] The file {table_name[12:]} saved successfully!')


async def run_parser(stopper_threshold=15, max_pages=None):
    stopper = 0
    page = 0
    while True:
        if max_pages is not None and page >= max_pages:
            break
        print(f'----------------- Downloading page {page} -----------------')
        table_urls = await get_tables_urls(page)

        tasks_for_downloads = [
            asyncio.create_task(download_xls(f"https://spimex.com/{table_url}"))
            for table_url in table_urls
        ]
        table_names = await asyncio.gather(*tasks_for_downloads)

        tasks_for_parse = [
            asyncio.create_task(parse_table(table_name))
            for table_name in table_names
        ]
        results = await asyncio.gather(*tasks_for_parse)

        stopper += results.count(False)
        if stopper >= stopper_threshold:
            break

        print('-----------------------------------------------------------\n')
        page += 1
