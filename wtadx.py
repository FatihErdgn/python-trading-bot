import pandas as pd
import numpy as np
from ta.trend import ADXIndicator

class AverageDirectionalIndex:   
    def __init__(self, df, adx_smoothing=14, di_length=14):
        self.df = df
        self.adx_smoothing = adx_smoothing
        self.di_length = di_length

    # @staticmethod
    # def fix_nan(value):
    #     return value if not pd.isna(value) else 0
    
    def wilders_smoothing(self, data, period):
        result = data.copy()
        for i in range(len(data)):
            if i < period - 1:
                result[i] = float('nan')
            elif i == period - 1:
                result[i] = data[i-period+1:i+1].mean()
            else:
                result[i] = (result[i-1] * (period - 1) + data[i]) / period
        return result
    
    def talib_adx(self): #Ta-lib kütüphanesini kullanarak otomatik hesaplama yapıyor
        
        adx_indicator = ADXIndicator(self.df['high'], self.df['low'], self.df['close'], self.di_length, fillna=True)
        talib_adx = adx_indicator.adx()
    
        return talib_adx
        
    def dirmov(self):
        up = self.df['high'].diff()
        down = -self.df['low'].diff()

        plus_dm = up.where((up > down) & (up > 0), 0)
        minus_dm = down.where((down > up) & (down > 0), 0)

        hl = self.df['high'] - self.df['low']
        hc = abs(self.df['high'] - self.df['close'].shift(1))
        lc = abs(self.df['low'] - self.df['close'].shift(1))
    
        truerange = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    
        truerange_smoothed = self.wilders_smoothing(truerange, self.di_length)
        plus_smoothed = (100 * self.wilders_smoothing(plus_dm, self.di_length) / truerange_smoothed).fillna(0)
        minus_smoothed = (100 * self.wilders_smoothing(minus_dm, self.di_length) / truerange_smoothed).fillna(0)
    
        return plus_smoothed, minus_smoothed


    def adx(self):
        plus, minus = self.dirmov()
        sum_di = plus + minus
        adx = self.wilders_smoothing(100 * abs(plus - minus) / sum_di.replace(0, 1), self.adx_smoothing)

        return adx
    
    def calculate(self):
        self.df['talib_adx'] = self.talib_adx()
        self.df['adx'] = self.adx()
        
        return self.df[['time','high','low','close','talib_adx','adx']]
    

class WaveTrend:
    def __init__(self, df):
        self.df = df
        self.wt1_wt2 = pd.DataFrame()
        self.n1 = 9
        self.n2 = 26

    def compute_wt1_wt2(self):
        # HLC3 Average
        self.df['ap'] = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        
        # EMA of HLC3
        self.df['esa'] = self.df['ap'].ewm(span=self.n1, adjust=False).mean()
        
        # D value
        self.df['d'] = (self.df['ap'] - self.df['esa']).abs().ewm(span=self.n1, adjust=False).mean()
        
        # CI value
        self.df['ci'] = (self.df['ap'] - self.df['esa']) / (0.015 * self.df['d'])
        
        # TCI value
        self.df['tci'] = self.df['ci'].ewm(span=self.n2, adjust=False).mean()
        
        # wt1 and wt2 values
        self.df['wt1'] = self.df['tci']
        self.df['wt2'] = self.df['wt1'].rolling(window=4).mean()

        return self.df[['wt1', 'wt2']]
    
    def compute(self):
        
        self.wt1_wt2 = self.compute_wt1_wt2() 
        cross_condition = ((self.wt1_wt2['wt1'].shift(1) < self.wt1_wt2['wt2'].shift(1)) & (self.wt1_wt2['wt1'] > self.wt1_wt2['wt2'])) | (self.wt1_wt2['wt1'].shift(1) > self.wt1_wt2['wt2'].shift(1)) & (self.wt1_wt2['wt1'] < self.wt1_wt2['wt2'])
        
        # Assign red or lime based on condition
        self.df['cross_point'] = 'na'
        self.df.loc[cross_condition & (self.wt1_wt2['wt2'] - self.wt1_wt2['wt1'] > 0), 'cross_point'] = 'Short'
        self.df.loc[cross_condition & (self.wt1_wt2['wt2'] - self.wt1_wt2['wt1'] <= 0), 'cross_point'] = 'Long'
        
        return self.df[['time','close','wt1','wt2','cross_point']]



