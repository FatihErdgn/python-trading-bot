import json
from binance.client import Client
import pandas as pd
import datetime


class BinanceFuturesBot:
    def __init__(self, credentials_path):
        with open(credentials_path, 'r') as file:
            credentials = json.load(file)
            self.recvWindow = 10000

        self.client = Client(credentials["BinanceKeys"]["API_KEY"],
                             credentials["BinanceKeys"]["API_SECRET"], tld='com')

        self.check_connection_status()

    def check_connection_status(self):
        try:
            self.client.futures_ping()

        except Exception as e:
            print("Hesap bağlantısında sorun var.",str(e))
            
    # def get_max_prescision(self,symbol):
    #     info = self.client.futures_exchange_info()

    #     requestedFutures = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DYDXUSDT']
    #     print(
    #         {si['symbol']:si['quantityPrecision'] for si in info['symbols'] if si['symbol'] in requestedFutures}
    #     )
    
    def get_max_precision(self, symbol):
        info = self.client.futures_exchange_info()
    
        # Eğer info bir liste döndürüyorsa, her bir item için kontrol yap
        for item in info['symbols']:
            if item['symbol'] == symbol:
                return item['quantityPrecision']

        return None  # Eğer uygun sembol bulunamazsa None döndür

    def get_account_balance(self):

        futures_balances = self.client.futures_account_balance()
        usdt_balance = next(
            (balance for balance in futures_balances if balance['asset'] == 'USDT'), None)

        if usdt_balance:
            available_balance = float(usdt_balance['availableBalance'])
            total_balance = float(usdt_balance['balance'])
            #print(f"USDT Available Balance: {available_balance}")
            #print(f"USDT Total Balance: {total_balance}")
        else:
            print("USDT bakiye bilgisi bulunamadı.")
        return available_balance,total_balance
    

    def get_active_futures_positions(self):
        active_pos = self.client.futures_position_information()
    
        # Boş bir DataFrame oluşturuluyor
        columns = ['Symbol', 'Position Amount','Position Amount USD', 'Entry Price', 'Unrealized Profit']
        df = pd.DataFrame(columns=columns)
    
        for position in active_pos:
            if float(position['positionAmt']) != 0:  # Pozisyon miktarı 0 olmayanları ekler
                symbol = position['symbol']
                position_amt = position['positionAmt']
                position_amt_usd = float(position['positionAmt']) * float(position['entryPrice'])
                entry_price = position['entryPrice']
                unrealized_profit = position['unRealizedProfit']
            
                # DataFrame'e yeni bir satır oluşturuluyor
                new_row = pd.DataFrame({
                    'Symbol': [symbol],
                    'Position Amount': [position_amt],
                    'Position Amount USD':[position_amt_usd],
                    'Entry Price': [entry_price],
                    'Unrealized Profit': [unrealized_profit]
                    })
            
                # yeni satırı ana DataFrame'e ekleniyor
                df = pd.concat([df, new_row], ignore_index=True)
            
        return df


    def get_candlestick_data(self, symbol, timeframe, qty):     
        raw_data = self.client.get_klines(                  
            symbol=symbol, interval=timeframe, limit=qty)
        converted_data = []
        # raw_data = self.client.futures_klines(                  
        #     symbol=symbol, interval=timeframe, limit=qty)
        # converted_data = []
        
        for candle in raw_data:
            readable_time = datetime.datetime.fromtimestamp(
                candle[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            converted_candle = {
                "time": readable_time,
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5])
            }

            converted_data.append(converted_candle)

            df = pd.DataFrame(converted_data)
        return df
    
    #Create Binance Futures Position Order
    #Long Order
    def create_long_order (self,symbol, quantity):
        longOrder = self.client.futures_create_order(
        symbol=symbol,
        side=Client.SIDE_BUY,
        type=Client.ORDER_TYPE_MARKET,
        recvWindow = self.recvWindow,
        quantity=quantity)
        return longOrder
    
    #Short order
    def create_short_order(self,symbol, quantity):
        shortOrder = self.client.futures_create_order(
        symbol=symbol,
        side=Client.SIDE_SELL,
        type=Client.ORDER_TYPE_MARKET,
        recvWindow = self.recvWindow,
        quantity=quantity)
        return shortOrder
    


if __name__ == "__main__":
    CREDENTIALS_PATH = "C:/Users/Administrator/Desktop/BINANCE_TRADING_BOT/settings.json"
    bot = BinanceFuturesBot(CREDENTIALS_PATH)
