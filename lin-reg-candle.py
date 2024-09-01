import numpy as np

class HumbleLinRegCandles:

    def __init__(self, dataframe):
        self.df = dataframe.copy()

    def linreg(self, arr, length):
        x = np.arange(length)
        slope, intercept = np.polyfit(x, arr[-length:], 1)
        return intercept + slope * (length - 1)

    def process(self, signal_length=9, sma_signal=True, lin_reg=True, linreg_length=9):
        if lin_reg:
            self.df['bopen'] = self.df['open'].rolling(window=linreg_length).apply(lambda x: self.linreg(x, linreg_length), raw=True)
            self.df['bhigh'] = self.df['high'].rolling(window=linreg_length).apply(lambda x: self.linreg(x, linreg_length), raw=True)
            self.df['blow'] = self.df['low'].rolling(window=linreg_length).apply(lambda x: self.linreg(x, linreg_length), raw=True)
            self.df['bclose'] = self.df['close'].rolling(window=linreg_length).apply(lambda x: self.linreg(x, linreg_length), raw=True)
        else:
            self.df['bopen'] = self.df['open']
            self.df['bhigh'] = self.df['high']
            self.df['blow'] = self.df['low']
            self.df['bclose'] = self.df['close']

        self.df['r'] = self.df['bopen'] < self.df['bclose']

        if sma_signal:
            self.df['signal'] = self.df['bclose'].rolling(window=signal_length).mean()
            
            self.df['Buy_Signal'] = self.df['signal'] < (self.df['close'])
            self.df['Sell_Signal'] = self.df['signal'] > (self.df['close'])
                        
                
        else:
            self.df['signal'] = self.df['bclose'].ewm(span=signal_length, adjust=False).mean()

        return self.df