import websockets
import asyncio
import requests
import json
import time
import httpx 

class WarningLoadSymbols(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class Settings:
    def __init__(self, queue, connections=None):
        self.symbols = self.load_symbols()
        self.connections = connections if connections else 3
        self.connect_websocket = 450
        self.list_queue = queue
        self.data = {}
    
    async def one_load_settings(self):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get('https://api.binance.com/api/v3/ticker/bookTicker')
                data = response.json()
                for symbol in data:
                    if float(symbol['bidPrice']) != 0 or float(symbol['askPrice']) != 0.0:
                            self.data[symbol['symbol']] = {
                                'bid': symbol['bidPrice'], 
                                'ask': symbol['askPrice'],
                                'askVolume': symbol['askQty'], 
                                'bidVolume': symbol['bidQty']
                            }
            except:
                raise WarningLoadSymbols('________________WARNING________________\nНе удалось загрузить начальные данные о символах.')
            
    def load_symbols(self) -> list:
        response = requests.get('https://api.binance.com/api/v3/exchangeInfo').json()
        symbols_res = []
        for symbol in response['symbols']:
            if symbol['status'] == 'TRADING':
                symbols_res.append(symbol['symbol'])
        return symbols_res

    def get_symbols_connect(self):
        symbols_list = []
        iteration = 0 
        for i in self.symbols:
            if iteration != self.connect_websocket:
                symbols_list.append(i)
                self.symbols.remove(i)
                iteration += 1
        return symbols_list
    
    async def monitoring_data(self):
        while True:
            print(len(self.data.keys()))
            await asyncio.sleep(1)

    async def connect_websockets(self):
        websockets_objects = []
        for index in range(1, self.connections + 1):
            symbols = self.get_symbols_connect()
            object = Websocket(index, self.data, self.list_queue[index-1], symbols)
            websockets_objects.append(object)
        tasks = [self.one_load_settings]
        for object in websockets_objects:
            tasks.append(object.run)
        await asyncio.gather(*[task() for task in tasks])

    def run(self): 
        asyncio.run(self.connect_websockets())


 
class Websocket:
    def __init__(self, index: int, data_load: dict, queue, symbols: list) -> None:
        self.index = index
        self.shared_dict = data_load
        self.queue = queue
        self.symbols =  symbols
        self.url = self.load_url()
        self.asyncio_queue = asyncio.Queue()
    
    def load_url(self):
        url = 'wss://stream.binance.com:9443/ws'
        for symbol in self.symbols:
            symbol_add = f'/{symbol.lower()}@bookTicker'
            url += symbol_add
        return url

    async def handle_message(self):
        asyncio.create_task(self.connect())
        while True:
            message = await self.asyncio_queue.get()
            data = json.loads(message)
            self.shared_dict[data['s']] = {
                'bid': data['b'],
                'ask': data['a'],
                'askVolume': data['A'],
                'bidVolume': data['B']
            } 
            try:
                self.queue.put(self.shared_dict, block=False)
            except Exception:
                continue

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.url) as websocket:
                    print(f'Websocket {self.index} - Соединение установлено')
                    while True:
                        message = await websocket.recv()
                        await self.asyncio_queue.put(message)
            except (websockets.ConnectionClosed, websockets.exceptions.InvalidStatusCode, TimeoutError):
                print(f'Websocket {self.index} Error. Reconnecting...')
                await asyncio.sleep(5)
    
    async def run(self):
        await asyncio.sleep(self.index + 2)
        await self.handle_message()

class ListenChannel:
    def __init__(self, data) -> None:
        self.data = data

    def get_key(self):
        api_key = ''
        listen_key_url = "https://api.binance.com/api/v3/userDataStream"
        headers = {
            "X-MBX-APIKEY": api_key
        }
        response = requests.post(listen_key_url, headers=headers)
        data = response.json()
        return data["listenKey"]

    async def connect_weboskcet_trades(self):
        listen_key = self.get_key()
        uri = f"wss://stream.binance.com:9443/ws/{listen_key}"
        symbols_tag = {}
        async with websockets.connect(uri) as websocket:
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    if data["e"] == "executionReport":
                        if data['X'] == 'FILLED':
                            key = f'{data["s"]}FILLED'
                            try:
                                tag = symbols_tag[key]
                                tag = int(tag) + 1
                            except KeyError:
                                tag = 0
                            self.data[key] = {
                                    'tag': tag,
                                    'symbol': data['s'], 
                                    'price': data['p'], 
                                    'quantity': data['q'], 
                                    'quantity2': data['Z'], 
                                    'side': data['S']
                                }
                            symbols_tag[key] = tag
                    
                except (websockets.ConnectionClosed, websockets.exceptions.InvalidStatusCode, TimeoutError):
                    await asyncio.sleep(5)
                    continue

    
def run_stream(queue):
    settings = Settings(queue)
    settings.run()

