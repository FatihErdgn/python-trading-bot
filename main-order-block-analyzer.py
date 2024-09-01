from connection import BinanceFuturesBot
import pandas as pd
import time
from reversalStrategy import ReversalStrategy
from hullSuiteEmaCross import HullSuiteEmaCross
##from linRegCandle import HumbleLinRegCandles
from orderBlockAnalyzer import OrderBlockAnalyzer
from OBVMACD import OBVMACD
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logger import Logger

symbolName = "BTC" #input("Botun kullanılacağı sembolü girin (BTC,ETH,LTC...): ").upper()
symbol = str(symbolName) + "USDT"
strateji = "2" #input("Kullanılacak strateji?  \n 1:Hull Suite + Ema Cross + Extreme Divergence Strategy \n 2: Reversal Strategy \n Seçin: ")
leverage = "12" #input("Kaldıraç büyüklüğü?: ")
timeframe = "5m" #input("timeframe (1m,3m,5m,15m,30m,45m,1h): ")
botUser = "Fatih"
quantity = 0
posCoin = 0

if strateji == "1":
    EmaFastVal = input("EmaFast: ")
    EmaSlowVal = input("EmaSlow: ")
    stopLoss = input("Stop Loss % : ")
pos_type = ""

#Connect to binance API
CREDENTIALS_PATH = "C:/Users/fther/OneDrive/Masaüstü/BINANCE_TRADING_BOT/settings.json"
trading_bot = BinanceFuturesBot(CREDENTIALS_PATH)
log = Logger(CREDENTIALS_PATH)
alert = False
T_F = pd.DataFrame()

inPositionLong = False
inPositionShort = False
posOpenTimeLong = None
posOpenTimeShort = None
position_amount_usd_open = 0
profitOrLoss = 0

while True:
    try:
        
        balances = trading_bot.get_account_balance()
        active_pos = trading_bot.get_active_futures_positions()
        raw_data = trading_bot.get_candlestick_data(symbol,timeframe, 100)
        
        if symbol in active_pos.iloc[:,0].values and T_F.empty:
            if (active_pos['Position Amount USD'] < 0).any():
                inPositionLong = False
                inPositionShort = True
                posOpenTimeLong = None
                posOpenTimeShort = raw_data['time'].iloc[-1]
                position_amount_usd_open = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount USD'].values)
                
            elif (active_pos['Position Amount USD'] > 0).any():
                inPositionLong = True
                inPositionShort = False
                posOpenTimeLong = raw_data['time'].iloc[-1]
                posOpenTimeShort = None
                position_amount_usd_open = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount USD'].values)
        
            
        #print(raw_data)
        
        def send_mail(symbol, pos_type):
            try:
                with open(CREDENTIALS_PATH, 'r') as file:
                    credentials = json.load(file)

                mailAddress = credentials['mailInfo']['mailAddress']
                password = credentials['mailInfo']['password']
                sendTo = credentials['mailInfo']['sendTo']
    
                # E-posta içeriğini HTML olarak oluştur
                html_content = """
                <html>
                    <head></head>
                    <body>
                        <h2>Binance Trading Bot: {} pozisyon tipi: {}</h2>
                        <p>{} paritesinde pozisyon {}! <b>Kar/Zarar durumu: {} USD</b></p>
                        {}
                    </body>
                </html>
                """.format(symbol,pos_type, symbol, "açıldı" if pos_type == "LONG" or pos_type == "SHORT" or pos_type == "ÖNCEDEN AÇILMIŞ" else "kapatıldı", profitOrLoss if pos_type != "ÖNCEDEN AÇILMIŞ" else "0", active_pos.to_html())

                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"Binance Trading Bot: {symbol}"
                msg["From"] = mailAddress
                msg["To"] = sendTo

                part1 = MIMEText(html_content, "html")
                msg.attach(part1)
                
                smtpServer = credentials['mailInfo']['smtpServer']
                port = credentials['mailInfo']['port']
                mail = smtplib.SMTP(smtpServer, port=port)
                mail.set_debuglevel(1)
                mail.ehlo()
                mail.starttls()
                mail.login(mailAddress, password)
                mail.sendmail(mailAddress, sendTo, msg.as_string())
                mail.quit()
                
            except Exception as e:
                    log.display(str(e),botUser=botUser)
            
        max_precision = trading_bot.get_max_precision(symbol)
            
        
        #Hull Suite + EMA Cross Strategy
        if strateji == "1":
            strat = HullSuiteEmaCross(raw_data)
            "..."
            
        elif strateji == "2":
            orderBlock = OrderBlockAnalyzer(raw_data)
            orderBlocksignals = orderBlock.identify_order_blocks()
            hullSuite = HullSuiteEmaCross(raw_data)
            rsi = hullSuite.calculate_rsi(14)
            
            if T_F.empty:
                T_F = pd.DataFrame({'Buy_Signal': [False], 'Sell_Signal': [False]})
            else:
                if 'Buy_Signal' not in T_F.columns:
                    T_F['Buy_Signal'] = False
                if 'Sell_Signal' not in T_F.columns:
                    T_F['Sell_Signal'] = False


            if linRegSignal['Buy_Signal'].iloc[-1] == True and obvMacdSignal['Buy_Signal'].iloc[-1] == True:
                T_F['Buy_Signal'].iloc[0] = True
                T_F['Sell_Signal'].iloc[0] = False
            elif linRegSignal['Sell_Signal'].iloc[-1] == True and obvMacdSignal['Sell_Signal'].iloc[-1] == True:
                T_F['Buy_Signal'].iloc[0] = False
                T_F['Sell_Signal'].iloc[0] = True
            else:
                T_F['Buy_Signal'].iloc[0] = False
                T_F['Sell_Signal'].iloc[0] = False
                
            """ if inPositionLong == True and (raw_data['time'].iloc[-1] != posOpenTimeLong) and (obvMacdSignal['Sell_Signal'].iloc[-2:] == True).any():
                active_pos = trading_bot.get_active_futures_positions()
                posCoin = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount'].values[0])

                closePosLong = trading_bot.create_short_order(symbol, quantity=posCoin)
                profitOrLoss = float(active_pos[active_pos.iloc[:, 0] == symbol]['Unrealized Profit'].values)
                        
                pos_type = "LONG CLOSED"
                inPositionLong = False
                alert = False
                send_mail(symbol, pos_type)
            
            elif inPositionShort == True and (raw_data['time'].iloc[-1] != posOpenTimeShort) and (obvMacdSignal['Buy_Signal'].iloc[-2:] == True).any():
                active_pos = trading_bot.get_active_futures_positions()
                posCoin = -1*float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount'].values[0])
                
                closePosShort = trading_bot.create_long_order(symbol, quantity=posCoin)
                profitOrLoss = float(active_pos[active_pos.iloc[:, 0] == symbol]['Unrealized Profit'].values)

                pos_type = "SHORT CLOSED"
                inPositionShort = False
                alert = False
                send_mail(symbol, pos_type) """
            
        
        #Reversal Strategy
        elif strateji == "3":
            strat = ReversalStrategy(raw_data)
            strat.calculate()
            signalData = strat.get_signals()
            T_F = signalData.iloc[-1:, 1:3].copy()
            

        print("Sinyal durumu (False: VAR , True: YOK):\n" + str(T_F))
            
        if active_pos.empty or (not active_pos.empty and symbol not in active_pos.iloc[:, 0].values):
                    
            if balances[0] > 10 and balances[0] < 100 and T_F['Buy_Signal'].iloc[0] == True and T_F['Sell_Signal'].iloc[0] == False: #Eğer herhangi bir satır eşit mi diye kontrol edilecekse: (T_F['Buy_Signal'] == True).any()) 
                if max_precision == 0:
                    quantity = int(round((balances[0] / 100) * 100 * float(leverage) / (raw_data["close"].iloc[-1]),max_precision))
                else:
                    quantity = round((balances[0] / 100) * 100 * float(leverage) / (raw_data["close"].iloc[-1]),max_precision)
                print(symbol + " adet " + str(quantity))
                buyOrder = trading_bot.create_long_order(symbol, quantity)
                pos_type = "LONG"
                inPositionLong = True
                alert = True
                posOpenTimeLong = raw_data['time'].iloc[-1]
                active_pos = trading_bot.get_active_futures_positions()
                profitOrLoss = float(active_pos[active_pos.iloc[:, 0] == symbol]['Unrealized Profit'].values)
                send_mail(symbol, pos_type)
                        
                position_amount_usd_open = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount USD'].values)
                        
                                

                        
            elif balances[0] > 10 and balances[0] > 100 and T_F['Buy_Signal'].iloc[0] == True and T_F['Sell_Signal'].iloc[0] == False:
                if max_precision == 0:
                    quantity = int(round((balances[0] / 100) * 80 * float(leverage) / (raw_data["close"].iloc[-1]),max_precision))
                else:
                    quantity = round((balances[0] / 100) * 80 * float(leverage) / (raw_data["close"].iloc[-1]),max_precision)
                print(symbol + " adet " + str(quantity))
                buyOrder = trading_bot.create_long_order(symbol, quantity)
                pos_type = "LONG"
                inPositionLong = True
                alert = True
                posOpenTimeLong = raw_data['time'].iloc[-1]
                active_pos = trading_bot.get_active_futures_positions()
                profitOrLoss = float(active_pos[active_pos.iloc[:, 0] == symbol]['Unrealized Profit'].values)
                send_mail(symbol, pos_type)
                        
                position_amount_usd_open = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount USD'].values)
                        
                        

                
            elif balances[0] > 10 and balances[0] < 100 and T_F['Buy_Signal'].iloc[0] == False and T_F['Sell_Signal'].iloc[0] == True:
                if max_precision == 0:
                    quantity = int(round((balances[0] / 100) * 100 * float(leverage) / (raw_data["close"].iloc[-1]),max_precision))
                else:
                    quantity = round((balances[0] / 100) * 100 * float(leverage) / (raw_data["close"].iloc[-1]),max_precision)
                print(symbol + " adet " + str(quantity))
                sellOrder = trading_bot.create_short_order(symbol, quantity)
                pos_type = "SHORT"
                inPositionShort = True
                alert = True
                posOpenTimeShort = raw_data['time'].iloc[-1]
                active_pos = trading_bot.get_active_futures_positions()
                profitOrLoss = float(active_pos[active_pos.iloc[:, 0] == symbol]['Unrealized Profit'].values)
                send_mail(symbol, pos_type)
                        
                position_amount_usd_open = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount USD'].values)
                        
                            
                        
            elif balances[0] > 10 and balances[0] > 100 and T_F['Buy_Signal'].iloc[0] == False and T_F['Sell_Signal'].iloc[0] == True:
                if max_precision == 0:
                    quantity = int(round((balances[0] / 100) * 80 * float(leverage) / (raw_data["close"].iloc[-1]),max_precision))
                else:
                    quantity = round((balances[0] / 100) * 80 * float(leverage) / (raw_data["close"].iloc[-1]),max_precision)
                print(symbol + " adet " + str(quantity))
                sellOrder = trading_bot.create_short_order(symbol, quantity)
                pos_type = "SHORT"
                inPositionShort = True
                alert = True
                posOpenTimeShort = raw_data['time'].iloc[-1]
                active_pos = trading_bot.get_active_futures_positions()
                profitOrLoss = float(active_pos[active_pos.iloc[:, 0] == symbol]['Unrealized Profit'].values)
                send_mail(symbol, pos_type)
                        
                position_amount_usd_open = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount USD'].values)                        

        elif not active_pos.empty and (active_pos['Symbol'] == symbol).any():
            if T_F['Buy_Signal'].iloc[0] == False and T_F['Sell_Signal'].iloc[0] == True and inPositionLong == True and (raw_data['time'].iloc[-1] != posOpenTimeLong):
                    
                active_pos = trading_bot.get_active_futures_positions()
                posCoin = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount'].values[0])

                closePosLong = trading_bot.create_short_order(symbol, quantity=posCoin)
                profitOrLoss = float(active_pos[active_pos.iloc[:, 0] == symbol]['Unrealized Profit'].values)
                        
                pos_type = "LONG CLOSED"
                inPositionLong = False
                alert = False
                send_mail(symbol, pos_type)
                        
                        


            elif T_F['Buy_Signal'].iloc[0] == True and T_F['Sell_Signal'].iloc[0] == False and inPositionShort == True and (raw_data['time'].iloc[-1] != posOpenTimeShort):
                        
                active_pos = trading_bot.get_active_futures_positions()
                posCoin = -1*float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount'].values[0])
                
                closePosShort = trading_bot.create_long_order(symbol, quantity=posCoin)
                profitOrLoss = float(active_pos[active_pos.iloc[:, 0] == symbol]['Unrealized Profit'].values)

                pos_type = "SHORT CLOSED"
                inPositionShort = False
                alert = False
                send_mail(symbol, pos_type)
                
                          
        
                
        if (inPositionLong == True or inPositionShort == True) and alert == False:
            
            position_amount_usd_open = float(active_pos[active_pos.iloc[:, 0] == symbol]['Position Amount USD'].values)
            log.display(f"{symbol} USDT paritesinde pozisyon açıldı! *{pos_type}* \n fiyat: {position_amount_usd_open} kullanici: ",botUser)
            log.display(active_pos,botUser)
            pos_type = "ÖNCEDEN AÇILMIŞ"
            send_mail(symbol, pos_type)
            alert = True
        else:
            print("POZİSYON ARANIYOR...")
        
    except Exception as e:
        log.display(str(e),botUser=botUser)
        log.display(str(posCoin),botUser=botUser)
        log.display(str(quantity),botUser=botUser)
        exception = e
        log.send_exception_mail(str(e))
        
    
    time.sleep(30)
    
