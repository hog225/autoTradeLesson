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


if __name__ == '__main__':
    result_df = getStockCode('kospi')
    result_df.to_csv('kospi.csv')
    print(result_df[['회사명', '종목코드']])