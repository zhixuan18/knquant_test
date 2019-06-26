###knquant笔试
import numpy as np
import pandas as pd
import math

Data_path = 'HS300 DATA.xlsx'

Data_hs300 = {}

def ReadData(data_path):
    Data = pd.read_excel(data_path)
    for i in range(len(math.ceil(Data.shape[1]/4))):
        stock_name = Data.iloc[0,4*i+1]
        stock_data = Data.iloc[4:,4*i:4*i+3]
        stock_data.columns = Data.iloc[2,4*i:4*i+3]
        stock_data.set_index('Date',inplace=True)
        Data_hs300[stock_name] = stock_data


