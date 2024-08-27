import requests
import time
import json


class Stream:
    """
    Синхронный класс
    """
    def __init__(self, queue=None) -> None:
        self.settings = self.get_symbols() 
        self.queue = queue if queue else {}

    def get_symbols(self) -> list:
        """
        Получает символы с биржи. Затем 
        генерирует массив с парами, которые 
        подходят для этого потока
        """
        symbols = requests.get('https://api.binance.com/api/v3/exchangeInfo').json()['symbols']
        curr = [i['baseAsset'] for i in symbols]
        settings = {}
        tickers_dict = {}
        for i in curr:
            tickers_dict[i] = [j['symbol'] for j in symbols if j['baseAsset'] == i]
        tickers_all = []
        for tickers_add in tickers_dict.values():
            tickers_all.append([j for j in tickers_add])
        tickers_iteration = []
        for iteration in tickers_all:
            for symbol in iteration:
                if symbol[-4:] == 'USDT':
                    for symbol2 in iteration:
                        if symbol != symbol2:
                            tickers_iteration.append([symbol, symbol2])
        for symbol in symbols:
            settings[symbol['symbol']] = {
                'symbol': symbol['baseAsset'],
                'symbol1': symbol['quoteAsset']
            }
        settings['symbols'] = tickers_iteration
        return settings

    def symbols_websocket(self, queue):
        while True:
            data = queue.get()
            start_iteration = time.time()
            for iteration in self.settings['symbols']:
                symbol = iteration[0]
                symbol2 = iteration[1]
                try:
                    pair2 = self.settings[symbol2]
                    symbol_price = data[symbol]['ask']
                    symbol2_price = data[symbol2]['bid']
                    try:
                        symbol3 = pair2['symbol1'] + 'USDT'
                        symbol3_price = data[symbol3]['bid']
                        symbol3_price = float(symbol2_price) * float(symbol3_price)
                    except KeyError:
                        symbol3 = 'USDT' + pair2['symbol1']
                        symbol3_price = data[symbol3]['ask']
                        symbol3_price = float(symbol2_price) / float(symbol3_price)
                    end = 100 - float(symbol_price) / float(symbol3_price) * 100
                    if end > 0.225:
                        continue
                except KeyError:
                    continue
            print('1 Время выполнения цикла: ', time.time() - start_iteration)

    def run(self):
        self.symbols_websocket(self.queue)

def run_stream_1(queue):
    object = Stream(queue)
    object.run()
