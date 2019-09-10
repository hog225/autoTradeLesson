# coding=utf-8

import pandas as pd
import numpy as np
from mpl_finance import candlestick_ohlc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import datetime
import os

class Cursor(object):
    def __init__(self, ax):
        self.ax = ax
        self.lx = ax.axhline(ls='dashed', lw=0.5, color='b')  # the horiz line
        self.ly = ax.axvline(ls='dashed', lw=0.5, color='b')  # the vert line

        self.txt = ax.text(0.7, 0.9, '', transform=ax.transAxes)

    def mouse_move(self, event):
        if not event.inaxes:
            return

        x, y = event.xdata, event.ydata
        # update the line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)

        self.txt.set_text('x=%1.2f, y=%1.2f' % (x, y))
        plt.draw()


class SnaptoCursor(object):
    """
    Like Cursor but the crosshair snaps to the nearest x,y point
    For simplicity, I'm assuming x is sorted
    """

    def __init__(self, ax, x, oclh, ax2=None, ax3=None):
        y = oclh['close']
        self.oclh = oclh
        self.ax = ax
        self.ax2 = ax2
        self.ax3 = ax3
        self.lx = ax.axhline(ls='dashed', lw=0.5, color='b')  # the horiz line
        self.ly = ax.axvline(ls='dashed', lw=0.5, color='b')  # the vert line

        self.ax2ly = ax2.axvline(ls='dashed', lw=0.5, color='b') if self.ax2 else None
        self.ax3ly = ax3.axvline(ls='dashed', lw=0.5, color='b') if self.ax3 else None

        self.x = x
        self.y = y
        # text location in axes coords

        self.ax.set_ylim((y.min() * (0.97), y.max() * (1.03)))
        self.txt = ax.text(0.7, 0.9, '', transform=ax.transAxes)

    def mouse_move(self, event):

        if not event.inaxes:
            return

        x, y = event.xdata, event.ydata

        indx = min(np.searchsorted(self.x, [x])[0], len(self.x) - 1)
        x = self.x[indx]
        y = self.y[indx]
        # update the line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)

        if self.ax2ly:
            self.ax2ly.set_xdata(x)
        if self.ax3ly:
            self.ax3ly.set_xdata(x)

        date_str = self.y.index[x].strftime('%Y-%m-%d')
        percentage = ((y - self.y[indx - 1]) / self.y[indx - 1]) * 100.0  # 전일 종가와 금일 종가
        self.txt.set_fontstyle('italic')
        self.txt.set_fontsize('x-small')
        o = self.oclh['open'][indx]
        h = self.oclh['high'][indx]
        l = self.oclh['low'][indx]
        self.txt.set_text('x: %s, Close: %1.2f, open:%1.2f\n,\
                        high: %1.2f, low:%1.2f\n, \
                        PERC = %1.2f' % (date_str, y, o, h, l, percentage))

        plt.draw()


class DrawLineOnClick(object):
    """
    Like Cursor but the crosshair snaps to the nearest x,y point
    For simplicity, I'm assuming x is sorted
    """
    lines = []

    def __init__(self, ax, x, pricing, sr_line):

        self.ax = ax
        self.oclh = pricing[['open', 'close', 'low', 'high']]
        self.x = x
        self.y = pricing['close']
        self.sr_line = sr_line
        self.point_cnt = 2  # 그래프를 그릴때 참조할 마커 포인터의 개수
        # self.ax.set_ylim((y.min()*(0.99), y.max()*(1.01)))

    def mouseClick(self, event):

        if not event.inaxes:
            return

        if event.dblclick:
            print('Double Click')
            try:
                self.lines.pop(0).remove()
                print('Remain Line %d ' % len(self.lines))
            except:
                print('No Line To Remove')

            return

        x, y = event.xdata, event.ydata

        indx = min(np.searchsorted(self.x, [x])[0], len(self.x) - 1)

        x_list = self.x
        point_x = self.x[indx]
        point_y = self.y[indx]

        o = self.oclh['open'][indx]
        h = self.oclh['high'][indx]
        l = self.oclh['low'][indx]
        c = point_y

        date_str = self.y.index[self.x[indx]].strftime('%Y-%m-%d')
        percentage = ((c - self.y[indx - 1]) / self.y[indx - 1]) * 100.0  # 전일 종가와 금일 종가

        for line_indic in self.sr_line:
            tmp_index = []
            for t in range(indx):
                if line_indic[t] > 0:
                    tmp_index.append(t)

            if len(tmp_index) >= self.point_cnt:

                x1 = self.x[tmp_index[-2]]
                x2 = self.x[tmp_index[-1]]

                y1 = self.y[tmp_index[-2]]
                y2 = self.y[tmp_index[-1]]

                y_list = (np.array(x_list) - x1) * ((y2 - y1) / (x2 - x1)) + y1
                print('Slop :', (y2 - y1) / (x2 - x1), 'last_x', x2, 'last_y', y2)

                self.lines.append(self.ax.axhline(y=y2, ls='dashed', lw=1, color='k'))  # 수평라인
                # line_list = self.ax.plot(x_list, y_list, ls='dashed', lw=1) # 기울기
                # self.lines.append(line_list[0])
            elif len(tmp_index) == 1:

                y2 = self.y[tmp_index[-1]]
                self.lines.append(self.ax.axhline(y=y2, ls='dashed', lw=1, color='k'))  # 수평라인

            plt.draw()


def plot_candles(pricing, title=None, volume_bars=False, volume_tech=None, color_function=None,
                 technicals=None, marker=None, line_52=None, sep_technicals=None, sr_line=None):
    """ Plots a candlestick chart using quantopian pricing data.

    Author: Daniel Treiman

    Args:
      pricing: A pandas dataframe with columns ['open_price', 'close_price', 'high', 'low', 'volume']
      title: An optional title for the chart
      volume_bars: If True, plots volume bars
      color_function: A function which, given a row index and price series, returns a candle color.
      technicals: A list of additional data series to add to the chart.  Must be the same length as pricing.
      marker : list or serise
      line_52 : 52일 고점 저점
      sr_line : list 저항선, 지지선, 기준선 등등
    """

    # y 데이터에 시가 종가 고가 저가 표시 하기
    # 저항선 지지선 Y 에 vertical 라인으로 표시 하기  hello

    def default_color(index, open_price, close_price, low, high):
        return 'r' if open_price[index] > close_price[index] else 'g'

    color_function = color_function or default_color
    technicals = technicals or []
    sep_technicals = sep_technicals or []
    marker = marker or []
    line_52 = line_52 or []
    sr_line = sr_line or []
    volume_tech = volume_tech or []

    marker_shape = ['v', '^', 'v', '^', 'o', '<', '>', '1', '2', '3', '4', '8', 's', 'P', 'p', '*', 'x', 'X']
    marker_color = ['m', 'k', 'y', 'c', 'r', 'g', 'b', '#0F0F0F0F']
    marker_label = ['up', 'down', 'p_up', 'p_down', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n',
                    'n']
    open_price = pricing['open']
    close_price = pricing['close']
    low = pricing['low']
    high = pricing['high']
    oclh = pricing[['open', 'close', 'low', 'high']]
    oc_min = pd.concat([open_price, close_price], axis=1).min(axis=1)
    oc_max = pd.concat([open_price, close_price], axis=1).max(axis=1)

    if volume_bars and sep_technicals:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1, 1]})
    elif volume_bars:
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        ax3 = None
    elif sep_technicals:
        fig, (ax1, ax3) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        ax2 = None
    else:
        fig, ax1 = plt.subplots(1, 1)
        ax2 = None
        ax3 = None

    if title:
        ax1.set_title(title)
    x = np.arange(len(pricing))
    candle_colors = [color_function(i, open_price, close_price, low, high) for i in x]


    ohlc = np.vstack((list(range(len(pricing))), pricing.values.T)).T
    
    candlestick_ohlc(ax1, ohlc, width=0.6, colorup='r', colordown='b')

    ax1.xaxis.grid(True, ls='dashed')
    ax1.xaxis.set_tick_params(which='major', length=3.0, direction='in', top='off')

    for idx, y_value in enumerate(line_52):
        ax1.axhline(y=y_value, ls='dashed', lw=0.7, color='g')

    # Assume minute frequency if first two bars are in the same day.
    frequency = 'minute' if (pricing.index[1] - pricing.index[0]).days == 0 else 'day'
    time_format = '%Y-%m-%d'
    if frequency == 'minute':
        time_format = '%H:%M'
    # Set X axis tick labels.
    date_print_list = []
    k = 0
    for date in pricing.index:
        if k % 10 == 0:
            date_print_list.append(date.strftime(time_format))
        else:
            date_print_list.append('')
        k = k + 1

    xdate = [i.strftime(time_format) for i in pricing.index]

    def mydate(x, pos):
        try:
            return xdate[int(x)]
        except IndexError:
            return ''

    # plt.xticks(x, date_print_list, rotation='vertical')
    plt.xticks(x, [date.strftime(time_format) for date in pricing.index], rotation='vertical')
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(10))
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(mydate))
    # ax1.format_xdata = mdates.DateFormatter('%Y-%m-%d')

    for indicator in technicals:
        ax1.plot(x, indicator)

    k = 0
    for marker_indic in marker:
        tmp_index = []
        for t in range(len(marker_indic)):
            if marker_indic[t] > 0:
                tmp_index.append(t)

        ax1.plot(tmp_index, close_price[tmp_index],
                 marker_shape[k], markersize=7, color=marker_color[k], label=marker_label[k])
        k += 1

    if volume_bars:
        volume = pricing['volume']
        volume_scale = None
        scaled_volume = volume
        if volume.max() > 1000000:
            volume_scale = 'M'
            scaled_volume = volume / 1000000
        elif volume.max() > 1000:
            volume_scale = 'K'
            scaled_volume = volume / 1000
        ax2.bar(x, scaled_volume, color=candle_colors)
        volume_title = 'Volume'
        if volume_scale:
            volume_title = 'Volume (%s)' % volume_scale
        ax2.set_title(volume_title)
        ax2.xaxis.grid(True, ls='dashed')
        if volume_tech:
            for v_tech in volume_tech:
                v_tech_scale = v_tech
                if volume.max() > 1000000:
                    v_tech_scale = v_tech / 1000000
                elif volume.max() > 1000:
                    v_tech_scale = v_tech / 1000
                ax2.plot(x, v_tech_scale)

    if sep_technicals:
        for s_technic in sep_technicals:
            ax3.plot(x, s_technic)
        ax3.set_title('sep_technical')
        ax3.xaxis.grid(True, ls='dashed')
        # ax3.axhline(y=0, ls='dashed', lw=0.7, color='g')
        # slowd slowK 일때는 해지
        if s_technic.max() > 20:
            ax3.axhline(y=80, ls='dashed', lw=0.7, color='g')
            ax3.axhline(y=20, ls='dashed', lw=0.7, color='g')
        else:
            ax3.axhline(y=0, ls='dashed', lw=0.7, color='g')

    cursor = SnaptoCursor(ax1, x, oclh, ax2, ax3)
    click = DrawLineOnClick(ax1, x, pricing, sr_line)
    # cursor = SnaptoCursor(ax1, x, close_price)
    # cursor = Cursor(ax1)
    plt.connect('motion_notify_event', cursor.mouse_move)
    plt.connect('button_press_event', click.mouseClick);

    # fig.autofmt_xdate()
    # plt.legend(loc=0)
    plt.show()


class LineBuilder:
    def __init__(self, line):
        self.line = line
        self.xs = list(line.get_xdata())
        self.ys = list(line.get_ydata())
        self.cid = line.figure.canvas.mpl_connect('button_press_event', self)

    def __call__(self, event):
        print(('click', event))
        if event.inaxes != self.line.axes: return
        self.xs.append(event.xdata)
        self.ys.append(event.ydata)
        self.line.set_data(self.xs, self.ys)
        self.line.figure.canvas.draw()


def enter_axes(event):
    print(('enter_axes', event.inaxes))
    event.inaxes.patch.set_facecolor('yellow')
    event.canvas.draw()


def leave_axes(event):
    print(('leave_axes', event.inaxes))
    event.inaxes.patch.set_facecolor('white')
    event.canvas.draw()


def enter_figure(event):
    print(('enter_figure', event.canvas.figure))
    event.canvas.figure.patch.set_facecolor('red')
    event.canvas.draw()


def leave_figure(event):
    print(('leave_figure', event.canvas.figure))
    event.canvas.figure.patch.set_facecolor('grey')
    event.canvas.draw()


def csvToDataFrameForChart(file_name):


    df = pd.read_csv(file_name)

    df.index = df['Date'].apply(pd.to_datetime) # Date 의 Dtype을 Datetime 형식으로 변경 해야함
    ch_df = df[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
    ch_df.columns = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
    ch_df = ch_df.tz_localize("UTC")
    return ch_df

if __name__ == "__main__":
    dfNaver = csvToDataFrameForChart('naver.csv')
    # dfNaver = csvToDataFrameForChart('naver.csv')
    plot_candles(dfNaver)


