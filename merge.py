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


def get_all_tickers():  # все тикеры фьючерсов
    global global_all_tickers
    all_tickers = []  # список с всеми тикерами
    symbol = session.get_instruments_info(  # запрос по апи
        category="linear",
        status="Trading",
    )
    request = symbol.get('result').get('list')  # Достаем нужную инфу
    for i in request:
        if '-' in i.get('symbol'):  # Удаление опционов
            request.remove(i)
            continue
        else:
            all_tickers.append(i.get('symbol'))  # Добавление всех тикеров в локальную переменную
            global_all_tickers.append(i.get('symbol'))  # Добавление всех тикеров в глокальную переменную
    return all_tickers


th.Thread(target=get_all_tickers).start()  # отдельный поток под все тикер


def show_ticker(window_id):  # При выборе тикеров в меню они показываются
    dpg.configure_item(window_id, visible=True)


def hide_ticker(window_id):  # Если тикер не выбран, то он скрывается
    dpg.configure_item(window_id, visible=False)


# TODO сделать обновление таблиц, а не бесконечный их вывод
# TODO позиционирование окон внутри окна скринера

all_open_ticker = []


def vol_screener(message, volume_usdt):
    ask = message.get('data').get('a')
    bid = message.get('data').get('b')
    ticker = message.get('data').get('s')
    if ticker in all_open_ticker:
        pass

    else:
        all_open_ticker.append(ticker)
        with dpg.child_window(label=ticker, width=200, height=230, parent='Main') as window_id:
            render_table(ask, bid, volume_usdt, window_id, ticker)



def render_table(ask, bid, volume_usdt, window_id, ticker):
    with dpg.table(label=f'{ticker}_table', header_row=True, row_background=True) as table_id:
        dpg.add_table_column(label='price')
        dpg.add_table_column(label='volume')
        dpg.add_table_column(label='vol_usdt')
        askflag = False
        counter = -1
        filtask = []
        for i in ask:
            if float(i[0]) * float(i[1]) < volume_usdt:
                continue
            else:
                filtask.append(i)
                askflag = True
        for ii in filtask[3::-1]:
            counter += 1
            with dpg.table_row():
                for j in range(0, 2):
                    dpg.add_text(ii[j])
                for k in range(0, 1):
                    dpg.add_text(str(int(float(ii[0]) * float(ii[1]))))
            dpg.set_table_row_color(table=table_id, row=counter, color=[255, 0, 0, 125])
        bidflag = False
        counter2 = counter
        filtbid = []
        for i in bid:
            if float(i[0]) * float(i[1]) < volume_usdt:
                continue
            else:
                filtbid.append(i)
                bidflag = True
        for ii in filtbid[:4:]:
            counter2 += 1
            with dpg.table_row():
                for j in range(0, 2):
                    dpg.add_text(ii[j])
                for k in range(0, 1):
                    dpg.add_text(str(int(float(ii[0]) * float(ii[1]))))
            dpg.set_table_row_color(table=table_id, row=counter2, color=[0, 255, 0, 125])
    if (askflag is False) and (bidflag is False):
        dpg.delete_item(window_id)
    else:
        pass


def get_tic(ticker):  # парсим и инфы о минимальной цене шага по тикеру
    tic = session.get_instruments_info(  # парсим инфу о тикерах
        category="linear",
        symbol=ticker
    )
    tic = tic.get('result')
    tic = tic.get('list')
    tic = tic[0]
    tic = tic.get('priceFilter')
    tic = tic.get('tickSize')
    return tic


def handle_message(message):
    volume_usdt = dpg.get_value('volume_in_usdt')
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

with dpg.window(tag="Main", label='Volume in USDT', width=800, height=200):  # Окно скринера по объему в баксах
    with dpg.menu_bar():  # Верхнее меню в скринере объема
        with dpg.menu(label="Token"):
            for i in get_all_tickers():
                dpg.add_checkbox(label=i)
            pass
        with dpg.menu(label="Settings"):
            dpg.add_input_int(label="Volume in USDT", tag='volume_in_usdt', default_value=300000, step=10000,
                              step_fast=100000, min_clamped=True, min_value=0)
            with dpg.tooltip("volume_in_usdt"):
                dpg.add_text("click +10.000\nCTRL+click +100.000")

        with dpg.menu(label="Start"):
            dpg.add_button(label="Start", tag='start', callback=start_code)
            dpg.add_button(label="Stop", tag='stop')

dpg.create_viewport(title='Screener', width=815, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
