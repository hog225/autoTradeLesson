import pandas as pd
from pandas_datareader import data
import os
from datetime import datetime


def getStockCode(market):
    if market == 'kosdaq':
        url_market = 'kosdaqMkt'
    elif market == 'kospi':
        url_market = 'stockMkt'
    else:
        print('invalid market ')
        return

    url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13&marketType=%s' % url_market
    df = pd.read_html(url, header=0)[0]

    return df

def getStockPrice(market, companyNameList = []):
    dirName = "stockPriceData"
    # -------------- dirName을 가진 폴더가 없으면 폴더를 만듬 -----------
    try:
        if not (os.path.isdir(dirName)):
            os.makedirs(os.path.join(dirName))
    except OSError as e:
        print("Failed to create directory!!!!!", e)
        return

    # -------------- 저장한 종목 코드가 담겨있는 CSV 파일을 Open -----------
    csv_file_name = market + '.csv'
    try:
        df = pd.read_csv(csv_file_name)
    except:
        print ('No file ')
        return

    # -------------- 종목코드를 Yahoo 가 이해할 수 있는 코드로 변환 -----------
    suffix = '.KS' if market == 'kospi' else '.KQ'
    df_nameAndCode = df[['회사명', '종목코드']]
    df_nameAndCode['종목코드'] = df_nameAndCode['종목코드'].astype(str)
    df_nameAndCode['종목코드'] = df_nameAndCode['종목코드'].str.zfill(6) + suffix

    # -------------- 전체종목 가져오기 -----------
    if companyNameList == []:
        for idx, dat in df_nameAndCode.iterrows():
            try:
                df_stockPrice = data.get_data_yahoo(dat['종목코드'])
                fileName = os.path.join(dirName, dat['회사명'] + '.csv')
                df_stockPrice.to_csv(fileName)
                print(dat['회사명'], ' Saved')

            except Exception as e:
                print(dat['회사명'], e)

    # -------------- companyNameList 에 정의된 종목만 가져오기 -----------
    else:
        for companyName in companyNameList:
            try:
                idx = df_nameAndCode['회사명'].tolist().index(companyName)
                df_stockPrice = data.get_data_yahoo(df_nameAndCode['종목코드'][idx])
                fileName = os.path.join(dirName, df_nameAndCode['회사명'][idx] + '.csv')
                df_stockPrice.to_csv(fileName)
                print(df_nameAndCode['회사명'][idx], ' Saved')
            except Exception as e:
                print(e)




if __name__ == '__main__':
    # result_df = getStockCode('kospi')
    # result_df.to_csv('kospi.csv')
    # result_df = getStockCode('kosdaq')
    # result_df.to_csv('kosdaq.csv')

    # getStockPrice('kosdaq') # 전체 kospi 주가를 가져옴
    getStockPrice('kospi', ['신세계', '삼성전자'])# List 안의 종목만 가져옴
