from pandas_datareader import data

# '035420.KS' = Naver종목코드.KospiCode
naver = data.get_data_yahoo('035420.KS')
print(naver.head())
print(naver.tail())

naver.to_csv('naver.csv')
naver.to_excel('naver.xlsx')
naver.to_pickle('naver.pickle')