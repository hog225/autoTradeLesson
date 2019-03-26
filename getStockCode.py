import pandas as pd


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

def getStockPrice(market, companyName = ''):

    csv_file_name = market + '.csv'
    try:
        df = pd.read_csv(csv_file_name)
    except:
        print ('invalid market')
        return
    df_nameAndCode = df[['회사명', '종목코드']]

    if companyName == '':
        for idx, data in df_nameAndCode.iterrows():
            print(data['회사명'])
            
    else:
        try:
            idx = df_nameAndCode['회사명'].tolist().index(companyName)
            print(df_nameAndCode['종목코드'][idx])
        except:
            print ('invalid Company Name')
            return


if __name__ == '__main__':
    #result_df = getStockCode('kospi')
    #result_df.to_csv('kospi.csv')
    #print(result_df[['회사명', '종목코드']])

    getStockPrice('kospi')