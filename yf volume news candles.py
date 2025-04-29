########################################################
# Stocks
########################################################
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pytz
import wikipediaapi
#import sys
#import os
import requests
import pandas as pd
import plotly.graph_objs as go
from flask_mail import Mail, Message
import opencage.geocoder
from datetime import datetime,timedelta
from timezonefinder import TimezoneFinder
import json
import mysql.connector
import re
import socket
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pandas.io.json import json_normalize
import plotly.express as px
import secrets
import time
import numpy as np
from markupsafe import Markup
import yfinance as yf


@app.route('/templates/stocks')
def stocks():
    
    connection = mysql.connector.connect(
        host="",
        user="",
        password="",
        database=""
    )

    query = "SELECT Symbol,date,Close,Volume,industry,sector,Price_Change,open,high,low FROM stocks;"

    sp500_90day = pd.read_sql(query, connection)
    # sp500_90day = sp500_90day.replace([np.inf, -np.inf, np.nan], 0)
    sp500_90day['Close'] = sp500_90day['Close'].astype(float)
    sp500_90day['Volume'] = sp500_90day['Volume'].astype(float)
    sp500_90day['Price_Change'] = sp500_90day['Price_Change'].astype(float)

    # sp500_90day['90daychange'] = sp500_90day.groupby("Symbol")['Close'].pct_change().cumsum() * 100
    sp500_90day['90daychange'] = sp500_90day['Close'].pct_change().cumsum() * 100

    sp500_90day = sp500_90day.replace([np.inf, -np.inf, np.nan], 0)

    sp_industry = sp500_90day.groupby("industry")["Price_Change"].mean()
    sp_sector = sp500_90day.groupby("sector")["Price_Change"].mean()

    sp500_day = sp500_90day[sp500_90day['date'] == sp500_90day['date'].max()]

    volume_day = sp500_day.groupby("Symbol")["Volume"].max()
    volume_day = volume_day.sort_values(ascending=False).reset_index(drop = False)

    volume_90day = sp500_90day.groupby("Symbol")["Volume"].mean()
    volume_90day = volume_90day.sort_values(ascending=False).reset_index(drop = False)
    volume_90day = volume_90day.rename(columns={"Volume": "Volume_90day"})

    volume_change = pd.merge(volume_day, volume_90day,
    left_on=['Symbol'],
    right_on =['Symbol'],
    how='left')

    volume_change['Volume/Average'] = (volume_change['Volume']/volume_change['Volume_90day'])
    volume_change = volume_change.sort_values(by = 'Volume/Average', ascending=False).reset_index(drop = True)

    Most_Volume_Symbol = volume_change['Symbol'][0]
    #Summary = sp500_90day[sp500_90day['Symbol'] == Most_Volume_Symbol]


    symbol = Most_Volume_Symbol

    volume_change_top10 = volume_change.head(10)

    ticker = yf.Ticker(Most_Volume_Symbol)

    SummaryText = ticker.info
    SummaryText = pd.DataFrame.from_dict(SummaryText, orient='index')
    SummaryText = SummaryText.transpose()
    SummaryText = (SummaryText['longBusinessSummary'].iloc[0])

    symbol = Most_Volume_Symbol
    ticker = yf.Ticker(symbol)
    news = (ticker.news)

    html_string = ""
    for dictionary in news:
        print(dictionary['title'])

        html_string += dictionary['title'] + "<br>"

    safe_html_string = Markup(html_string)

    mvp_df = sp500_90day[sp500_90day['Symbol'] == symbol]

    fig = go.Figure(data=[go.Candlestick(x=mvp_df['date'],
                                     open=mvp_df['open'],
                                     close=mvp_df['Close'],
                                     high=mvp_df['high'],
                                     low=mvp_df['low'])])

    fig.update_xaxes(type='category')
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(color='white'),
        yaxis=dict(color='white'),
        showlegend=False,
        xaxis_rangeslider_visible=False)
    fig.update_xaxes(showgrid=False, zeroline=False)  
    fig.update_yaxes(showgrid=False, zeroline=False)

    # stock_graph_html = fig.to_html(full_html=False)

    connection.close()

    return render_template('stocks.html',SummaryText = SummaryText,Most_Volume_Symbol = Most_Volume_Symbol,safe_html_string = safe_html_string,stock_plot=fig.to_html(full_html=False))

