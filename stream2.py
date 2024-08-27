import requests
import time
import json
from decimal import Decimal
import math

class Stream2:
    """
    Синхронный класс
    """
    def __init__(self, queue=None) -> None:
        self.settings = self.get_symbols() 
        self.queue = queue if queue else {}
        self.profit = {'all': 0}

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
                for symbol2 in iteration:
                    if symbol2[-4:] == 'USDT':
                        if symbol != symbol2:
                            tickers_iteration.append([symbol, symbol2])
        settings = {}
        for symbol in symbols:
            settings[symbol['symbol']] = {
                'symbol': symbol['baseAsset'],
                'symbol1': symbol['quoteAsset'],
                'len': symbol['baseAssetPrecision']
            }  
        lot_size = {}
        for i in symbols:
            symbol = i['symbol']
            lot = i['filters']
            for j in lot:
                if j['filterType'] == 'LOT_SIZE':
                    lot_size[symbol] = j['stepSize']
        settings['lot_size'] = lot_size

        settings['symbols'] = tickers_iteration
        return settings

    def round_to_step(self, value, step):
        decimal_number = Decimal(value)
        step_size = Decimal(step)
        precision = -int(math.log10(step_size))
        formatted_number = format(decimal_number, f'.{precision}f')
        return float(formatted_number)

    def round_to_step2(self, value, step):
        step_size = Decimal(step)
        precision = -int(math.log10(step_size))
        formatted_number = format(value, f'.{precision}f')
        return float(formatted_number)

    def symbols_websocket(self, queue):
        while True:
            data = queue.get()
            start_iteration = time.time()
            for iteration in self.settings['symbols']:
                symbol = iteration[0]
                symbol2 = iteration[1]
                try:
                    pair2 = self.settings[symbol]    
                    symbol_price = data[symbol]['ask']
                    symbol2_price = data[symbol2]['bid']
                    try:
                        symbol3 = pair2['symbol1'] + 'USDT'
                        symbol3_price = data[symbol3]['ask']
                        symbol3_price = float(symbol_price) * float(symbol3_price)
                    except KeyError:
                        symbol3 = 'USDT' + pair2['symbol1']
                        symbol3_price = data[symbol3]['bid']
                        symbol3_price = float(symbol_price) / float(symbol3_price)
                    end = 100 - symbol3_price / float(symbol2_price) * 100
                    if end > 0.225: 
                        continue
                except KeyError:
                    continue
            print('2 Время выполнения цикла: ', time.time() - start_iteration)

    def run(self):
        self.symbols_websocket(self.queue)

def run_stream_2(queue):
    object = Stream2(queue)
    object.run()
