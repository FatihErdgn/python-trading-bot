import numpy as np

class ReversalStrategy:
    def __init__(self, dataframe):
        self.data = dataframe.copy()
        
    def calculate(self, ccimom_cross='CCI', ccimom_length=10, use_divergence=True, 
                  rsi_overbought=65, rsi_oversold=35, rsi_length=14, 
                  ema_period=200, band_multiplier=1.8):
        
        # CCI and Momentum calculation
        if ccimom_cross == 'Momentum':
            mom = self.data['close'].diff(ccimom_length)
        else:  # default to CCI
            typical_price = (self.data['close'] + self.data['high'] + self.data['low']) / 3
            ma = typical_price.rolling(window=ccimom_length).mean()
            md = typical_price.rolling(window=ccimom_length).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
            cci = (typical_price - ma) / (0.015 * md)

        # RSI calculation
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=rsi_length).mean()
        avg_loss = loss.rolling(window=rsi_length).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Entry Conditions
        oversold_ago = rsi.shift().between(0, rsi_oversold)
        overbought_ago = rsi.shift().between(rsi_overbought, 100)
        
        bullish_divergence_condition = (rsi > rsi.shift()) & (rsi.shift() < rsi.shift(2))
        bearish_divergence_condition = (rsi < rsi.shift()) & (rsi.shift() > rsi.shift(2))
        
        if ccimom_cross == 'Momentum':
            long_entry_condition = mom.gt(0) & oversold_ago & (~use_divergence | bullish_divergence_condition)
            short_entry_condition = mom.lt(0) & overbought_ago & (~use_divergence | bearish_divergence_condition)
        else:  # default to CCI
            long_entry_condition = cci.gt(0) & oversold_ago & (~use_divergence | bullish_divergence_condition)
            short_entry_condition = cci.lt(0) & overbought_ago & (~use_divergence | bearish_divergence_condition)

        # EMA for strategy conditions
        ema100 = self.data['close'].ewm(span=100, adjust=False).mean()

        # Define trading signals based on the original indicator's entry conditions
        self.data['Buy_Signal'] = long_entry_condition & (self.data['close'] <= ema100)
        self.data['Sell_Signal'] = short_entry_condition & (self.data['close'] >= ema100)

    def get_signals(self):
        return self.data[['close', 'Buy_Signal', 'Sell_Signal']]

