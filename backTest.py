import pandas as pd
import talib as TA
import numpy as np
import math
from dateutil import relativedelta
import requests
import xml.etree.ElementTree as ET
import datetime

JONBER = 1  #1차
MACD = 3    #1차
RSI = 4     #1차
STOCH = 5   #1차

BUY = 2.0
SELL = -2.0


def getStockValueFromNaver(stock_code, reqtype, count= 14531, date=None):
    url = 'https://fchart.stock.naver.com/sise.nhn?symbol=%s&timeframe=day&startTime=20021101&count=%d&requestType=%d' % (stock_code, count, reqtype)
    r = requests.get(url)
    root = ET.fromstring(r.text)

    df_org = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'AdjClose', 'Volume'])
    for data in root.findall("./chartdata/item"):
        stockVal = data.attrib['data'].split('|')
        stockVal[0] = datetime.datetime.strptime(stockVal[0], "%Y%m%d").date()
        stockVal.append(None)

        df_new = pd.DataFrame([stockVal], columns=['Date', 'Open', 'High', 'Low','AdjClose', 'Volume', 'Close'])
        df_org = df_org.append(df_new, ignore_index=True, sort= False)

    return df_org

def getGoldDeadPosition(se_line1, se_line2):
    se_signal = np.sign(se_line1 - se_line2)
    se_signal[se_signal == 0] = 1
    se_signal = se_signal - se_signal.shift()
    # 2, -2 로 구성된 시리즈
    return se_signal

def getGoldDeadLineBoundaryPosition(se_signal, base_signal, buy_line, sell_line):
    # slowd 중 기준라인 사이의 값은 영으로 만든다
    if buy_line != sell_line:
        se_signal.loc[(base_signal > buy_line) & (base_signal < sell_line)] = 0
        # BUY LINE 밑에있는 매도 신호는 지운다
        se_signal[(base_signal <= buy_line) & (base_signal != 0) & (se_signal == -2)] = 0
        # SELL LINE 위에 있는 매수 신호는 지운다 .
        se_signal[(base_signal >= sell_line) & (base_signal != 0) & (se_signal == 2)] = 0
    else:
        se_signal[(base_signal <= buy_line) & (base_signal != 0) & (se_signal == -2)] = 0
        # SELL LINE 위에 있는 매수 신호는 지운다 .
        se_signal[(base_signal > sell_line) & (base_signal != 0) & (se_signal == 2)] = 0

    se_signal[np.isnan(se_signal)] = 0.0
    # testDf = pd.DataFrame({'A':se_signal, 'B':slowd, 'C':tmp_se_signal})
    return se_signal

def getTradePointFromMomentum(tech_anal_code, df_stock_val):
    base_line = []
    df_stock_val['trade'] = 0
    if tech_anal_code == JONBER:
        df_stock_val.loc[df_stock_val.index[0], 'trade'] = BUY
        df_stock_val.loc[df_stock_val.index[-1], 'trade'] = SELL

    # MACD
    elif tech_anal_code == MACD:
        se_macd, se_macdsignal, se_macdhist = TA.MACD(df_stock_val.AdjClose, fastperiod=12, slowperiod=26, signalperiod=9)
        se_macd = se_macd.round(2)
        se_macdsignal = se_macdsignal.round(2)
        tmpd = se_macd.copy()

        # MACD 가 Sig
        se_signal = getGoldDeadPosition(se_macd, se_macdsignal)
        se_signal = getGoldDeadLineBoundaryPosition(se_signal, tmpd, 0, 0)

        df_stock_val['trade'] = se_signal
        # -2.0 DeadCross 2.0 GoldCross SELL, BUY


        base_line = [0]
    elif tech_anal_code == RSI:
        real = TA.RSI(df_stock_val.AdjClose, timeperiod=14)
        se_30_sig = getGoldDeadPosition(real, 30)
        se_30_sig[se_30_sig == 2] = 0
        se_30_sig[se_30_sig == -2] = 2

        se_70_sig = getGoldDeadPosition(real, 70)
        se_70_sig[se_70_sig == -2] = 0
        se_30_sig[se_70_sig == 2] = -2

        se_signal = se_30_sig + se_70_sig
        df_stock_val['trade'] = se_signal

        base_line = [50]
    # STHOCH
    elif tech_anal_code == STOCH:
        SELL_LINE = 70
        BUY_LINE = 30

        slowk, slowd = TA.STOCH(df_stock_val.High, df_stock_val.Low, df_stock_val.AdjClose,\
                                fastk_period=12, slowk_period=5, slowk_matype=0, slowd_period=5, slowd_matype=0)
        slowk = slowk.round(2)
        slowd = slowd.round(2)
        tmpd = slowd.copy()

        se_signal = getGoldDeadPosition(slowk, slowd)

        # Slow D 가 25% 이하에서 %K 가 %d 를 상향 돌파시 매수
        # Slow D 가 75% 이상에서 %K 가 %d 를 하향 돌파시 매도
        se_signal= getGoldDeadLineBoundaryPosition(se_signal, tmpd, BUY_LINE, SELL_LINE)
        df_stock_val['trade'] = se_signal


        base_line = [50]

    print('Trade List : ')
    print(df_stock_val['trade'][df_stock_val['trade'] != 0.0])
    return df_stock_val, base_line

def makeResultData(df_stock_val, balance):
    buyList = []
    sellList = []

    se_trade = df_stock_val['trade'][df_stock_val['trade'] != 0.0]
    if len(se_trade[se_trade == 2].index) == 0:
        return buyList, sellList, pd.Series(), pd.Series(), pd.Series()
    first_buy_idx = se_trade[se_trade == 2].index[0]

    df_stock_val['Balance'] = 0.0
    df_stock_val['Asset'] = 0.0
    df_stock_val['StockCount'] = 0.0

    if first_buy_idx == 0:
        df_stock_val.loc[0, ['Balance', 'Asset', 'StockCount']] = balance, balance, 0
    else:
        df_stock_val.loc[0:first_buy_idx , ['Balance', 'Asset', 'StockCount']] = balance, balance, 0

    beforeIdx = first_buy_idx
    #for idx, value in se_trade.loc[first_buy_idx:].items():
    se_idx_list = se_trade.loc[first_buy_idx:].index
    print(se_idx_list)
    for idx, realIdx in enumerate(se_idx_list):

        if idx == 0 or \
                se_trade.loc[realIdx] == BUY and \
                se_trade.loc[beforeIdx] != se_trade.loc[realIdx]:

            stock_count = math.floor(balance / df_stock_val.loc[realIdx].AdjClose)
            balance -= stock_count * df_stock_val.loc[realIdx].AdjClose
            print('buy ', 'Before Trade IDX ', beforeIdx, 'Current Trade IDX: ', realIdx, 'Stock Price: ', df_stock_val.loc[realIdx].AdjClose,
                  'Stock Count : ', stock_count, 'balance: ', balance)
            if idx == len(se_idx_list) - 1:
                df_stock_val.loc[realIdx: , ['Balance', 'Asset', 'StockCount']] = \
                    balance, balance + (df_stock_val.loc[realIdx:]['AdjClose']* stock_count), stock_count
                print('end BUY')
            else:
                next_idx = idx + 1
                for remain_idx in range(idx+1, len(se_idx_list)):
                    if se_trade.loc[se_idx_list[remain_idx]] == SELL:
                        next_idx = remain_idx
                        break

                if remain_idx == len(se_idx_list)-1:
                    df_stock_val.loc[realIdx:, ['Balance', 'Asset', 'StockCount']] = \
                        balance, balance + (df_stock_val.loc[realIdx:][
                                                'AdjClose'] * stock_count), stock_count

                else:
                    df_stock_val.loc[realIdx:se_idx_list[next_idx], ['Balance', 'Asset', 'StockCount']] = \
                        balance, balance + (df_stock_val.loc[realIdx:se_idx_list[next_idx]]['AdjClose'] * stock_count), stock_count
                print('NOW BUY NEXT Trade IDX ', next_idx)
            buyList.append([
                df_stock_val.loc[realIdx].Date.strftime("%Y-%m-%d"),
                df_stock_val.loc[realIdx].AdjClose
            ])

            beforeIdx = realIdx


        elif se_trade.loc[realIdx] == SELL and \
                se_trade.loc[beforeIdx] != se_trade.loc[realIdx]:

            stock_count = df_stock_val.loc[realIdx]['StockCount']
            balance += stock_count * df_stock_val.loc[realIdx].AdjClose
            asset = balance
            stock_count = 0
            print('sell ', 'Before Trade IDX ', beforeIdx, 'Current Trade IDX: ', realIdx, 'Stock Price: ',
                  df_stock_val.loc[realIdx].AdjClose, 'Stock Count : ', stock_count, 'balance: ', balance)
            if idx == len(se_idx_list) - 1:
                df_stock_val.loc[realIdx:, ['Balance', 'Asset', 'StockCount']] = \
                    balance, asset, stock_count
                print('end SELL')
            else:
                next_idx = idx + 1
                for remain_idx in range(idx+1, len(se_idx_list)):
                    if se_trade.loc[se_idx_list[remain_idx]] == BUY:
                        next_idx = remain_idx
                        break

                if remain_idx == len(se_idx_list) - 1:
                    df_stock_val.loc[realIdx:, ['Balance', 'Asset', 'StockCount']] = \
                        balance, asset, stock_count
                else:
                    df_stock_val.loc[realIdx:se_idx_list[next_idx], ['Balance', 'Asset', 'StockCount']] = \
                        balance, asset, stock_count
                print('NOW SELL NEXT Trade IDX ', next_idx)
            sellList.append([
                df_stock_val.loc[realIdx].Date.strftime("%Y-%m-%d"),
                df_stock_val.loc[realIdx].AdjClose
            ])

            beforeIdx = realIdx

    print(df_stock_val.head(3))
    print(df_stock_val.tail(3))

    # for i in df_stock_val['Asset'].iteritems():
    #     print(i)
    return buyList, sellList, df_stock_val['Balance'], df_stock_val['Asset'], df_stock_val['StockCount']

def getInvestPeriod(startDate, EndDate):
    r = relativedelta.relativedelta(EndDate, startDate)
    if r.years:
        period_str = '%d년 %d개월 %d일' % (r.years, r.months, r.days)
    elif r.months:
        period_str = '%d개월 %d일' % (r.months, r.days)
    elif r.days:
        period_str = '%d일' % (r.days)

    return period_str

def main(stockCode, techAnalCode, balance, count):
    df_stock_val = getStockValueFromNaver(stockCode, 0, count=count)
    # STR 데이터를 숫자 타입으로 변환
    df_stock_val[["Open", "High", "Low", "AdjClose", "Volume"]] = df_stock_val[["Open", "High", "Low", "AdjClose", "Volume"]].apply(pd.to_numeric)
    df_stock_val, base_line = getTradePointFromMomentum(techAnalCode, df_stock_val)
    makeResultData(df_stock_val, balance)

    org_asset = df_stock_val.iloc[0].Asset
    last_asset = df_stock_val.iloc[-1].Asset
    added_asset = last_asset - org_asset
    final_yield = 100 * (added_asset / org_asset)
    str_invest_period = getInvestPeriod(df_stock_val.iloc[0].Date, df_stock_val.iloc[-1].Date)
    print('++++++++++결과+++++++++++++')
    print('초기 자산 : ', org_asset)
    print('마지막 자산 : ', last_asset)
    print('증가된 자산 : ', added_asset)
    print('수익률 : ', final_yield)
    print('투자일시 : ', df_stock_val.iloc[0].Date, '~', df_stock_val.iloc[-1].Date)
    print('투자기간 : ', str_invest_period)

if __name__ == '__main__':
    main('005930', JONBER, 1000000, 500)
