import numpy as np

class OBVMACDIndicator:

    def __init__(self, df):
        self.df = df
        self.calculate_obv_macd()

    def ema(self, series, length):
        return series.ewm(span=length, min_periods=1, adjust=False).mean()

    def dema(self, series, length):
        ma1 = self.ema(series, length)
        ma2 = self.ema(ma1, length)
        return 2 * ma1 - ma2
    
    def adjust_signals_rowwise(self):
        last_buy_signal_index = None
        last_sell_signal_index = None

        for idx, row in self.df.iterrows():
            if row['Buy_Signal']:
                last_buy_signal_index = idx
            if row['Sell_Signal']:
                last_sell_signal_index = idx
            
            if last_buy_signal_index and (not last_sell_signal_index or last_buy_signal_index > last_sell_signal_index):
                self.df.at[idx, 'Buy_Signal'] = True
            elif last_sell_signal_index and (not last_buy_signal_index or last_sell_signal_index > last_buy_signal_index):
                self.df.at[idx, 'Sell_Signal'] = True
            else:
                self.df.at[idx, 'Sell_Signal'] = False
                self.df.at[idx, 'Buy_Signal'] = False

    def calculate_obv_macd(self):
        window_len = 28
        price_spread = self.df['high'] - self.df['low']
        price_spread_std = price_spread.rolling(window=window_len).std()

        obv = (self.df['close'].diff().fillna(0).apply(np.sign) * self.df['volume']).cumsum()
        v_len = 14
        smooth = obv.rolling(window=v_len).mean()
        v_spread = (obv - smooth).rolling(window=window_len).std()

        shadow = (obv - smooth) / v_spread * price_spread_std

        self.df['out'] = np.where(shadow > 0, self.df['high'] + shadow, self.df['low'] + shadow)

        len10 = 1
        len9 = 9
        self.df['OBVEMA'] = self.ema(self.df['out'], len10)
        self.df['DEMA'] = self.dema(self.df['OBVEMA'],len9)

        len26 = 26
        slow_ma = self.ema(self.df['close'], len26)
        self.df['MACD'] = self.df['DEMA'] - slow_ma
        self.df['diff'] = self.df['MACD'].diff()
        self.df['Buy_Signal'] = self.df['diff'] >= 5
        self.df['Sell_Signal'] = self.df['diff'] <= -5
        
        self.adjust_signals_rowwise()
        return self.df

    def get_dataframe(self):
        return self.df
