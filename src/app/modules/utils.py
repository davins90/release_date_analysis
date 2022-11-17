import pandas as pd
import streamlit as st
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import pytrends
import os
import time
import requests

from pytrends.request import TrendReq
from datetime import timedelta, date
from datetime import datetime as dt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import zscore

pio.renderers.default = 'iframe'
pd.set_option('display.max_rows',None)
pd.set_option('display.max_columns',None)
# pytrends = TrendReq()
pytrends = TrendReq(timeout=(10,25), retries=2, backoff_factor=0.1)
scaler = MinMaxScaler()

########################################
## 1.0 Data retrieval
def range_date(release_date):
    """
    
    """
    x = dt(int(release_date.split("-")[2]), int(release_date.split("-")[1]), int(release_date.split("-")[0]))
    start_date = x + timedelta(days=-2)
    end_date = x + timedelta(days=+4)
#     end_date = dt.toDay()
    start_date = start_date.strftime("%Y-%-m-%d")
    end_date = end_date.strftime("%Y-%-m-%d")
    return start_date, end_date

@st.cache(ttl=60)
def download_data(cat,version,start_date,end_date):
    """
    
    """
    inter = []
    try:
        if version == "Hourly":
            historicaldf = pytrends.get_historical_interest(cat, year_start=int(start_date.split("-")[0]), month_start=int(start_date.split("-")[1]), 
                                                            day_start=int(start_date.split("-")[2]), hour_start=0, 
                                                            year_end=int(end_date.split("-")[0]), month_end=int(end_date.split("-")[1]), day_end=int(end_date.split("-")[2]), 
                                                            hour_end=23, cat=0, geo='GB', gprop='', sleep=0)
            inter.append(historicaldf.drop(columns='isPartial'))
        else:
            pytrends.build_payload(kw_list=cat,cat=0,geo='GB',timeframe="{} {}".format(start_date,end_date))
            inter.append(pytrends.interest_over_time().drop(columns='isPartial'))
        time.sleep(15)
    except requests.exceptions.Timeout:
        print("Timeout search: extend time.sleep")
    ## finalize df
    df = pd.concat(inter,axis=1)
    return df

def principal_component_analysis(df):
    """
    
    """
    x = df.iloc[:,1:6]
    x2 = StandardScaler().fit_transform(x.values)
    x3 = pd.DataFrame(x2, index=x.index, columns=x.columns)
    pca = PCA(n_components=0.9,random_state=1)
    pca.fit(x3)
    var1 = pca.explained_variance_ratio_[0]
    sv1 = pca.singular_values_[0]
    comp = pd.DataFrame(pca.components_,columns=[x3.columns]).T
    comp = comp.reset_index()
    comp = comp.sort_values(by=0,ascending=False)
    comp = comp.rename(columns={'level_0':'Keyword',0:'Score1'})
    fig = px.bar(comp,x=comp['Keyword'],y=comp['Score1'],color=comp['Keyword'])
    fig.update_layout(
        title="Keywords Score Importance of the week",
        xaxis_title="Keywords searched",
        yaxis_title="Score")
    fig.update_layout(title_x=0.5)
    st.plotly_chart(fig, use_container_width=True)
    return var1, sv1

def pds_static(df):
    """
    
    """
    ris = []
    for i in df:
        if (i == 'Piracy Demand Index') | (i == 'gangs of london season 2'):
            mean = df[i].mean() # the higher the mean, the higher the activity
            std = df[i].std() # the higher the std, the higher the movements
            var = df[i].quantile(0.99) # check for extreme value
            pds = 0.4*mean + 0.2*std + 0.4*var
            ub = 40
            lb = 0
            pds2 = 100*((1-0)*(pds-lb)/(ub-lb)+lb)
            ris.append(pds2)
    return ris

