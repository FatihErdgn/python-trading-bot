import numpy as np

class adxLinRegCandles:

    def __init__(self, dataframe):
        self.df = dataframe.copy()

    def linreg(self, arr, length):
        x = np.arange(length)
        slope, intercept = np.polyfit(x, arr[-length:], 1)
        return intercept + slope * (length - 1)

    def process(self, signal_length=9, sma_signal=True, lin_reg=True, linreg_length=9):
        if lin_reg:
            self.df['badx'] = self.df['adx'].rolling(window=linreg_length).apply(lambda x: self.linreg(x, linreg_length), raw=True)
        else:
            self.df['badx'] = self.df['adx']


        if sma_signal:
            self.df['signal'] = self.df['badx'].rolling(window=signal_length).mean()
            
            self.df['Buy_Signal'] = self.df['signal'] < (self.df['adx'])
            self.df['Sell_Signal'] = self.df['signal'] > (self.df['adx'])
                        
                
        else:
            self.df['signal'] = self.df['badx'].ewm(span=signal_length, adjust=False).mean()

        return self.df