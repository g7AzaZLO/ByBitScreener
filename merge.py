from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP
import dearpygui.dearpygui as dpg
import threading as th
from config import api_key, api_secret
from time import sleep

dpg.create_context()

session = HTTP(api_key=api_key, api_secret=api_secret, testnet=False)  # создание API сессии

ws = WebSocket(  # создание WebSocket сессии
    testnet=False,
    channel_type="linear",
)

global_all_tickers = []  # список всех тикеров фьючерсов
volume_usdt = 0  # объем в баксах


def get_all_tickers():  # все тикеры фьючерсов
    global global_all_tickers
    all_tickers = []  # список с всеми тикерами
    symbol = session.get_instruments_info(  # запрос по апи
        category="linear",
        status="Trading",
    )
    request = symbol.get('result').get('list')  # Достаем нужную инфу
    for i in request:
        if '-' in i.get('symbol'):  # Удаление фьючерсов
            request.remove(i)
            continue
        else:
            all_tickers.append(i.get('symbol'))  # Добавление всех тикеров в локальную переменную
            global_all_tickers.append(i.get('symbol'))  # Добавление всех тикеров в глокальную переменную
    return all_tickers


th.Thread(target=get_all_tickers).start()  # отдельный поток под все тикер

#TODO перевернуть аски
def vol_screener(message, volume_usdt):
    ask = message.get('data').get('a')
    bid = message.get('data').get('b')
    ticker = message.get('data').get('s')
    with dpg.window(label=ticker):
        with dpg.table(header_row=True) as table_id:
            dpg.add_table_column(label='price')
            dpg.add_table_column(label='volume')
            dpg.add_table_column(label='vol_usdt')
            counter = 0
            for i in ask:
                counter+=1
                if float(i[0]) * float(i[1]) < volume_usdt:
                    continue
                else:
                    with dpg.table_row():
                        for j in range(0, 2):
                            dpg.add_text(i[j])
                        for k in range(0, 1):
                            dpg.add_text(str(int(float(i[0]) * float(i[1]))))
            for i in bid:
                if float(i[0]) * float(i[1]) < volume_usdt:
                    continue
                else:
                    with dpg.table_row():
                        for j in range(0, 2):
                            dpg.add_text(i[j])
                        for k in range(0, 1):
                            dpg.add_text(str(int(float(i[0]) * float(i[1]))))

def get_tic(ticker):  # парсим и инфы о минимальной цене шага по тикеру
    tic = session.get_instruments_info(  # парсим инфу о тикерах
        category="linear",
        symbol=ticker
    )
    tic = tic.get('result')  # начало поиска минмиального шага цены
    tic = tic.get('list')
    tic = tic[0]
    tic = tic.get('priceFilter')
    tic = tic.get('tickSize')
    return tic

#TODO убрать добавление бесконечного количества новых таблиц
def handle_message(message):
    volume_usdt = dpg.get_value('volume_in_usdt')  # ВСЕ ЧТО НИЖЕ - НЕ РАБОТАЕТ
    vol_screener(message, volume_usdt)



def websocket_thread(symbol):
    x = ws.orderbook_stream(
        depth=500,
        symbol=symbol,
        callback=handle_message
    )
    while True:
        sleep(0)


def start_code():
    global volume_usdt
    volume_usdt = dpg.get_value('volume_in_usdt')
    all_tickers = get_all_tickers()
    for i in all_tickers:
        th.Thread(target=websocket_thread, args=(i,)).start()
    while True:
        if len(all_tickers) != len(global_all_tickers):
            list_difference = []
            for element in global_all_tickers:
                if element not in all_tickers:
                    list_difference.append(element)
            for i in list_difference:
                th.Thread(target=websocket_thread, args=(i,)).start()
            all_tickers = global_all_tickers


with dpg.viewport_menu_bar():  # Верхнее меню в всем скринере
    with dpg.menu(label="File"):
        pass

    with dpg.menu(label="Settings"):
        pass

    with dpg.menu(label="Help"):
        pass

with dpg.window(tag="Main", label='Volume in USDT', width=800, height=200):  # Окно искриера по объему в баксах
    with dpg.menu_bar():  # Верхнее меню в скринере объема
        with dpg.menu(label="Tocken"):
            for i in get_all_tickers():
                dpg.add_checkbox(label=i)
            pass
        with dpg.menu(label="Settings"):
            dpg.add_input_int(label="Volume in USDT", tag='volume_in_usdt')  # callback=set_volume_in_usdt)
        with dpg.menu(label="Start"):
            dpg.add_button(label="Start", tag='start', callback=start_code)
            dpg.add_button(label="Stop", tag='stop')

dpg.create_viewport(title='Screener', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()