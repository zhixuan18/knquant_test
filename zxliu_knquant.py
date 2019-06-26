###knquant笔试
import numpy as np
import pandas as pd
import math

class Strategy_Halfday_reversal(object):
    def __init__(self,N=50):
        self.stock_hs300 = []
        self.Data_hs300 = None
        self.N = N

    def ReadData(self,file_data='HS300 DATA.xlsx'):
        "读取HS300 DATA数据"
        Data = pd.read_excel(file_data)
        Data_hs300_tmp = []
        for i in range(math.ceil(Data.shape[1] / 4)):
            stock = Data.iloc[0,4*i+1]
            self.stock_hs300.append(stock)
            stock_data = Data.iloc[4:, 4 * i:4 * i + 3]
            stock_data.columns = Data.iloc[2,4*i:4*i+3]
            stock_data.set_index('Date', inplace=True)
            stock_data.columns = pd.MultiIndex.from_product([[stock],Data.iloc[2,4*i+1:4*i+3]])
            Data_hs300_tmp.append(stock_data)
        self.Data_hs300 = pd.concat(Data_hs300_tmp,axis=1)
        return None

    def Cal_Ret(self):
        "计算open-to-close和close-to-open收益率"
        for stock in self.stock_hs300:
            self.Data_hs300.loc[:,(stock,'RET_OC')] = self.Data_hs300.loc[:,(stock,'close')]/self.Data_hs300.loc[:,(stock,'open')]-1
            self.Data_hs300.loc[:,(stock,'RET_CO')] = self.Data_hs300.loc[:,(stock,'open')]/self.Data_hs300.loc[:,(stock,'close')].shift(1)-1
        return None

    def Strategy_OC(self):
        "计算根据close-to-open收益率,持有期为night策略的每日收益率"
        pass

    def Strategy_CO(self):
        "计算根据open-to-close收益率,持有期为day策略的每日收益率"
        pass

    def Strategy_Evaluate(self,plot_=True):
        "策略评价,包括计算总收益率,年化收益率,收益率方差,夏普比率,最大回撤率,最大回撤期,策略每日换手率,画累计收益"
        pass

    def Bench_Ret(self):
        "将所有股票简单平均加权作为benchmark,计算benchmark的收益率"
        pass

    def Factor_Evaluate(self):
        "因子评价,包括计算IC,IR,分组收益率，"
        pass