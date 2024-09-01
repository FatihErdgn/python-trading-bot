import sys
import pandas as pd
import numpy as np
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import Callback, EarlyStopping
from tensorflow.keras.optimizers import SGD
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from sklearn.preprocessing import MinMaxScaler
from matplotlib.figure import Figure
import threading
import random
import csv
from datetime import datetime, timedelta
from math import sqrt
import yfinance as yf

end_date = datetime.now().strftime('%Y-%m-%d')

# Bitcoin'in tarihsel verilerini yfinance üzerinden çekme
btc_data = yf.download('BTC-USD', start='2023-12-01', end=end_date, interval='1h')

# Verileri CSV formatında kaydetme
btc_data.to_csv('C:/BTCdata/bitcoin_historical_data.csv')

# Veri yükleme ve tarih sütununu datetime'a dönüştürme
data = pd.read_csv('C:/BTCdata/bitcoin_historical_data.csv')
if 'Year' in data.columns:
    data = data.drop(columns='Year')
data['Datetime'] = pd.to_datetime(data['Datetime'])

# Sadece ikinci kolonu ölçeklendirmek için MinMaxScaler kullanımı
scaler = MinMaxScaler()

# DataFrame'in ikinci kolonunu al ve ölçeklendir
scaled_column = scaler.fit_transform(data.iloc[:, [4]])

# Ölçeklenmiş veriyi orijinal DataFrame'e geri yerleştir
data.iloc[:, 4] = scaled_column

# Veriyi günlük bazda gruplandırma
data.set_index('Datetime', inplace=True)

# Model Parametreleri (Günlük)
n_input = 500  # Geçmişteki gün sayısı
n_predict = 168  # Tahmin edilecek gün sayısı
n_features = 1  # Öznitelik sayısı (fiyat)

# Veri Hazırlama (Günlük)
def data_prep_daily(data, n_input, n_predict):
    X, y = [], []
    for i in range(len(data) - n_input - n_predict):
        end_ix = i + n_input
        out_end_ix = end_ix + n_predict
        seq_x, seq_y = data[i:end_ix].values, data[end_ix:out_end_ix].values
        X.append(seq_x)
        y.append(seq_y)
    return np.array(X).reshape(-1, n_input, n_features), np.array(y)

X_train, Y_train = data_prep_daily(data['Close'], n_input, n_predict)

early_stopping = EarlyStopping(patience=20)
# Model Oluşturma
model = Sequential()
model.add(LSTM(120, activation='tanh', input_shape=(n_input, n_features)))
model.add(Dense(60, activation='tanh'))
model.add(Dense(60, activation='sigmoid'))
model.add(Dense(n_predict))

# Model Derleme
model.compile(optimizer='adam', loss='mean_squared_error')

# Callback ve Plotting
losses = []
val_losses = []

class PlotLosses(Callback):
    def on_epoch_end(self, epoch, logs={}):
        losses.append(logs.get('loss'))
        val_losses.append(logs.get('val_loss'))
        window.update_figure()

class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=10, height=8, dpi=180):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

    def plot(self):
        self.axes.clear()
        self.axes.plot(losses, label='Training loss')
        self.axes.plot(val_losses, label='Validation loss')
        self.axes.legend(loc='upper right')
        padding = 10
        # Son değerleri kontrol et ve yalnızca geçerliyse yerleştir
        if val_losses and np.isfinite(val_losses[-1]):
            self.axes.scatter(len(val_losses)-1, val_losses[-1], color='red', s=5)
            self.axes.text(len(val_losses)-1, val_losses[-1] - padding, f' {val_losses[-1]:.3f}', verticalalignment='bottom', fontsize=7)
        
        if losses and np.isfinite(losses[-1]):
            self.axes.scatter(len(losses)-1, losses[-1], color='blue', s=5)
            self.axes.text(len(losses)-1, losses[-1] + padding, f' {losses[-1]:.3f}', verticalalignment='top', fontsize=7)

        self.draw()

# PyQt5 Uygulaması
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.left = 10
        self.top = 10
        self.title = 'Training and Validation Loss'
        self.width = 1024
        self.height = 768
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.canvas = PlotCanvas(self, width=5, height=4)
        self.canvas.move(0, 0)

        self.predict_60_button = QPushButton('60 Gün Tahmin Et ve Kaydet', self)
        self.predict_60_button.setGeometry(800, 700, 200, 30)
        self.predict_60_button.clicked.connect(self.make_prediction_60_days)

        self.show()

    def update_figure(self):
        self.canvas.plot()

    def make_prediction_60_days(self):
        # En son verileri al (örneğin, en son 120 hafta)
        last_data = data['Close'][-n_input:].values
        x_input = last_data.reshape((1, n_input, n_features))
        
        # Tahmin yap
        predicted_scaled_value = model.predict(x_input, verbose=0)[0]
        predicted_scaled_values_reshaped = predicted_scaled_value.reshape(-1, 1)
        predicted_prices = scaler.inverse_transform(predicted_scaled_values_reshaped)
    
        # Tahminlerin başlangıç tarihini belirle (örneğin, veri setindeki son tarihten sonraki hafta)
        last_date = data.index[-1]
        prediction_start_date = last_date + timedelta(hours=1)

        # Tahminleri kaydet
        self.save_to_csv(predicted_prices, prediction_start_date)

        # Doğruluk testi için tahminleri gerçek değerlerle karşılaştır
        # Örneğin, son 120 haftalık gerçek değerleri al
        real_values = data['Close'][-n_predict:].values
        accuracy = 100 * (1 - val_losses[-1]*val_losses[-1] / np.var(real_values))
        test_accuracy = 100 * (1 - val_losses[-1]*losses[-1] / np.var(real_values))
        print(f"Test Model Accuracy: {test_accuracy:.1f}%")
        print(f"Model Accuracy: {accuracy:.1f}%")


    def save_to_csv(self, predictions, start_date):
        with open('weekly_predictions.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Week Starting Date', 'Predicted Price'])
            for i, prediction in enumerate(predictions):
                week_start_date = start_date + timedelta(hours=i+1)
                writer.writerow([week_start_date.strftime('%Y-%m-%d'), prediction])


def train_model():
    model.fit(X_train, Y_train, epochs=1000, batch_size=32, validation_split=0.2, callbacks=[PlotLosses(),early_stopping])




app = QApplication(sys.argv)
window = App()
training_thread = threading.Thread(target=train_model)
training_thread.start()
sys.exit(app.exec_())
