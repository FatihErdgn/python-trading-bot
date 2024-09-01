import pandas as pd

class OrderBlockAnalyzer:
    def __init__(self, dataframe):
        self.data = dataframe.copy()
        
    def identify_order_blocks(self, periods=4, threshold=0.0, use_wicks=False):
        df = self.data
        ob_period = periods + 1
        df['bullishOB'] = (df['close'].shift(ob_period) < df['open'].shift(ob_period))
        df['bearishOB'] = (df['close'].shift(ob_period) > df['open'].shift(ob_period))
        ##print(df['close'].shift(ob_period))
    
        df['absmove'] = (abs(df['close'].shift(ob_period) - df['close'].shift(1)) / df['close'].shift(ob_period)) * 100
        df['relmove'] = df['absmove'] >= threshold
    
        df['upcandles'] = (df['close'] > df['open']).rolling(periods).sum()
        df['downcandles'] = (df['close'] < df['open']).rolling(periods).sum()
    
        df['OB_bull'] = df['bullishOB'] & (df['upcandles'] == periods) & df['relmove']
        df['OB_bear'] = df['bearishOB'] & (df['downcandles'] == periods) & df['relmove']
    
        df['OB_bull_high'] = df.apply(lambda x: x['high'] if (use_wicks and x['OB_bull']) else (x['open'] if x['OB_bull'] else None), axis=1)
        df['OB_bull_low'] = df.apply(lambda x: x['low'] if x['OB_bull'] else None, axis=1)
    
        df['OB_bear_high'] = df.apply(lambda x: x['high'] if x['OB_bear'] else None, axis=1)
        df['OB_bear_low'] = df.apply(lambda x: x['low'] if (use_wicks and x['OB_bear']) else (x['open'] if x['OB_bear'] else None), axis=1)
    
        signals = pd.DataFrame(index=df.index)
        signals['Buy_Signal'] = df['OB_bull']
        signals['Sell_Signal'] = df['OB_bear']
        signals['time'] = df['time']

        return signals

# Example usage:
# Assuming you have a pandas DataFrame 'data' with columns 'Open', 'High', 'Low', 'Close'
# analyzer = OrderBlockAnalyzer(data)
# signals = analyzer.identify_order_blocks()
# print(signals.tail())  # Display the latest signals
