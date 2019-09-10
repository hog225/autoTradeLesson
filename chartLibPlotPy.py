import plotly.graph_objects as go

import pandas as pd
from datetime import datetime

df = pd.read_csv('naver.csv')

fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])])

# fig['data'].push({
#     'type': 'scatter',
#     'mode': 'lines',
#     'x': df['Date'],
#     'y': df['Close']
# })
fig.update_layout(
    title='The Great Recession',
    yaxis_title='AAPL Stock',
    shapes = [dict(
        x0='2016-12-09', x1='2016-12-21', y0=0, y1=1, xref='x', yref='paper',
        line_width=2)],
    annotations=[dict(
        x='2016-12-09', y=0.05, xref='x', yref='paper',
        showarrow=False, xanchor='left', text='Increase Period Begins')]
)
fig.show()


