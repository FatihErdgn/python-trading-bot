import numpy as np
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

class HullSuiteEmaCross:
    def __init__(self, dataframe):
        self.data = dataframe.copy()

    def calculate_ema(self, period):
        ema = EMAIndicator(self.data['close'], period).ema_indicator()
        return ema
    
    def calculate_rsi(self,period):
        self.data['rsi'] = RSIIndicator(self.data['close'],period).rsi()
        return self.data[['close','time','rsi']]

    def calculate_ema_cross(self, EmaFastVal, EmaSlowVal):
        # Calculate EMA values
        self.data['EmaFast'] = self.calculate_ema(EmaFastVal)
        self.data['EmaSlow'] = self.calculate_ema(EmaSlowVal)
        self.data['rsi'] = self.calculate_rsi(14)
        
        # Fetch recent values
        prev2_ema_fast = self.data['EmaFast'].iat[-3]
        prev2_ema_slow = self.data['EmaSlow'].iat[-3]
        
        prev_ema_fast = self.data['EmaFast'].iat[-2]
        prev_ema_slow = self.data['EmaSlow'].iat[-2]
        prev_rsi = self.data['rsi'].iat[-2]

        # Check for EMA crossover
        if prev2_ema_fast < prev2_ema_slow and prev_ema_fast > prev_ema_slow and prev_rsi < 10:
            self.EmaCross = True
            self.long = True
            self.short = False
            self.data['Buy_Signal'] = self.long
            self.data['Sell_Signal'] = self.short


        elif prev2_ema_fast > prev2_ema_slow and prev_ema_fast < prev_ema_slow and prev_rsi > 90:
            self.EmaCross = True
            self.long = False
            self.short = True
            self.data['Buy_Signal'] = self.long
            self.data['Sell_Signal'] = self.short
    
    def get_signals_ema_cross(self):
        return self.data[['close', 'Buy_Signal', 'Sell_Signal']]

    @staticmethod
    def wma(series, period):
        weights = np.arange(1, period + 1)
        return series.rolling(period).apply(lambda x: np.dot(x, weights)/weights.sum(), raw=True)

    @staticmethod
    def ema(series, period):
        return series.ewm(span=period).mean()

    @staticmethod
    def HMA(src, length):
        return HullSuiteEmaCross.wma(2 * HullSuiteEmaCross.wma(src, int(length / 2)) - HullSuiteEmaCross.wma(src, length), int(np.sqrt(length)))

    @staticmethod
    def EHMA(src, length):
        return HullSuiteEmaCross.ema(2 * HullSuiteEmaCross.ema(src, int(length / 2)) - HullSuiteEmaCross.ema(src, length), int(np.sqrt(length)))

    @staticmethod
    def THMA(src, length):
        return HullSuiteEmaCross.wma(HullSuiteEmaCross.wma(src,int(length / 3)) * 3 - HullSuiteEmaCross.wma(src, int(length / 2)) - HullSuiteEmaCross.wma(src, length), length)

    @staticmethod
    def Mode(modeSwitch, src, length):
        if modeSwitch == "Hma":
            return HullSuiteEmaCross.HMA(src, length)
        elif modeSwitch == "Ehma":
            return HullSuiteEmaCross.EHMA(src, length)
        elif modeSwitch == "Thma":
            return HullSuiteEmaCross.THMA(src, int(length/2))
        else:
            return pd.Series([np.nan]*len(src))

    def generate_signals_Hull(self):
        src = self.data['close']
        length = 55
        lengthMult = 1.0
        modeSwitch = "Hma"

        hull = self.Mode(modeSwitch, src, int(length * lengthMult))
        
        self.data['HULL'] = hull
        self.data['Buy_Signal'] = self.data['HULL'] > self.data['HULL'].shift(1)
        self.data['Sell_Signal'] = self.data['HULL'] < self.data['HULL'].shift(1)

        # Sadece ilgili sütunları döndürelim
        return self.data[['close', 'Buy_Signal', 'Sell_Signal']]

