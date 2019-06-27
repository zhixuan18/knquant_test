###knquant笔试
#-*- coding: utf-8 -*-
import numpy as np
import pandas as pd
pd.set_option('display.max_columns',None)
import math
import matplotlib.pyplot as plt

class Strategy_Halfday_reversal(object):
    def __init__(self):
        self.stock_hs300 = [] #沪深300股票代码
        self.Data_hs300 = None #沪深300股票数据
        self._N = 50 #每次持有股票数量
        self.Bench_Ret = None #benchmark的收益率

    #可修改购买股票的数量
    @property
    def N(self):
        return self._N
    @N.setter
    def N(self,value):
        self._N = value

    # 读取HS300 DATA数据
    def ReadData(self,file_data='HS300 DATA.xlsx'):
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

    # 计算close-to-close,open-to-close和close-to-open收益率
    def Cal_Ret(self):
        for stock in self.stock_hs300:
            self.Data_hs300.loc[:,(stock,'Ret_CO')] = self.Data_hs300.loc[:,(stock,'close')]/self.Data_hs300.loc[:,(stock,'open')]-1
            self.Data_hs300.loc[:,(stock,'Ret_OC')] = self.Data_hs300.loc[:,(stock,'open')]/self.Data_hs300.loc[:,(stock,'close')].shift(1)-1
            self.Data_hs300.loc[:,(stock,'Ret_CC')] = self.Data_hs300.loc[:,(stock,'close')]/self.Data_hs300.loc[:,(stock,'close')].shift(1)-1
        return None

    # 计算根据close-to-open收益率,持有期为night策略的每日收益率
    def Strategy_CO(self):
        Strategy_CO_ret = pd.DataFrame(index=self.Data_hs300.index[1:-1],columns=['Strategy_CO_Ret'],dtype=np.float64)
        for i in range(len(self.Data_hs300) - 2):
            date = self.Data_hs300.index[i]
            Ret_CO_tmp = self.Data_hs300.loc[date, (slice(None), 'Ret_CO')]
            # 持有close-to-open收益率最低的N只股票
            Holding_Stock = Ret_CO_tmp.sort_values(ascending=True).iloc[:self._N].reset_index().level_0
            holding_date = self.Data_hs300.index[i+1]
            Strategy_CO_ret.iloc[i] = self.Data_hs300.loc[holding_date, (Holding_Stock, 'Ret_OC')].mean()
        return Strategy_CO_ret

    # 计算根据open-to-close收益率,持有期为day策略的每日收益率
    def Strategy_OC(self):
        Strategy_OC_ret = pd.DataFrame(index=self.Data_hs300.index[1:-1],columns=['Strategy_OC_Ret'],dtype=np.float64)
        for i in range(len(self.Data_hs300) - 2):
            date = self.Data_hs300.index[i+1]
            Ret_OC_tmp = self.Data_hs300.loc[date, (slice(None), 'Ret_OC')]
            # 持有close-to-open收益率最低的N只股票
            Holding_Stock = Ret_OC_tmp.sort_values(ascending=True).iloc[:self._N].reset_index().level_0
            holding_date = date
            Strategy_OC_ret.iloc[i] = self.Data_hs300.loc[holding_date, (Holding_Stock, 'Ret_CO')].mean()
        return Strategy_OC_ret

    # 计算最大回撤率和最大回撤期
    def Max_Drawdown(self,Ret_cum):
        Drawdown = Ret_cum/Ret_cum.cummax()
        max_drawdown = Drawdown.min()-1
        drawdown_end = Drawdown.idxmin()
        drawdown_begin = Drawdown.loc[:drawdown_end].idxmax()
        return (max_drawdown,drawdown_begin,drawdown_end)

    # 策略评价,包括计算总收益率,年化收益率,收益率方差,夏普比率,最大回撤率,最大回撤期,画累计收益
    def Strategy_Evaluate(self,name,Ret,plot_bench=False,bench_name='Bench_Ret_OC',save_fig=False,compound=True):
        # Ret为2年的收益率Series,plot_bench=True画出benchmark的收益率曲线,compound=True计算复利
        Result = pd.DataFrame(index=[name])
        Result['begin date'] = Ret.index[0]
        Result['end date'] = Ret.index[-1]
        if compound:
            Ret_cum = (Ret+1).cumprod()
            Result['annual return'] = Ret_cum.iloc[-1]**0.5-1
        else:
            Ret_cum = Ret.cumsum()+1
            Result['annual return'] = Ret_cum.iloc[-1]/2-1
        Result['total return'] = Ret_cum.iloc[-1]-1
        Result['daily return std'] = Ret.std()
        Result['mean/std of daily return'] = Ret.mean()/Ret.std()
        Drawdown_info = self.Max_Drawdown(Ret_cum)
        Result['Max Drawdown'] = Drawdown_info[0]
        Result['Max Drawdown begin'] = Drawdown_info[1]
        Result['Max Drawdown end'] = Drawdown_info[2]
        #绘图
        plt.figure(figsize=(12,6))
        x = Ret_cum.index
        ret_cum = Ret_cum.values
        plt.plot(ret_cum,linewidth=2,linestyle='-',label=name)
        if plot_bench:
            if compound:
                bench_cc = (self.Bench_Ret['Bench_Ret_CC']+1).cumprod().values
                bench = (self.Bench_Ret[bench_name]+1).cumprod().values
            else:
                bench_cc = (self.Bench_Ret['Bench_Ret_CC'].cumsum()+1).values
                bench = (self.Bench_Ret[bench_name].cumsum()+1).values
            plt.plot(bench_cc,linewidth=2,linestyle='-',label='Bench_Ret_CC')
            plt.plot(bench,linewidth=2,linestyle='-',label=bench_name)
        plt.legend(loc=0)
        plt.xlim(-1,len(x)+1)
        x_tick = range(0,len(x),20)
        x_label = [x[i].strftime('%Y-%m-%d') for i in x_tick]
        plt.xticks(x_tick,x_label,rotation=0)
        plt.title(name)
        if save_fig:
            plt.savefig(name+'.png')
        else:
            plt.show()
        return Result

    # 将所有股票简单平均加权作为benchmark,计算benchmark的收益率
    def Cal_Bench_Ret(self):
        Bench_Ret = pd.DataFrame(index=self.Data_hs300.index[1:-2],columns=['Bench_Ret_CC','Bench_Ret_CO','Bench_Ret_OC'],dtype=np.float64)
        for date in self.Data_hs300.index[1:-2]:
            Bench_Ret.loc[date,'Bench_Ret_CC'] = self.Data_hs300.loc[date,(slice(None),'Ret_CC')].mean()
            Bench_Ret.loc[date,'Bench_Ret_CO'] = self.Data_hs300.loc[date, (slice(None),'Ret_CO')].mean()
            Bench_Ret.loc[date,'Bench_Ret_OC'] = self.Data_hs300.loc[date, (slice(None),'Ret_OC')].mean()
        self.Bench_Ret = Bench_Ret
        return None

    # 因子评价,包括计算IC,IR,分组收益率
    def Factor_Evaluate(self):
        pass
