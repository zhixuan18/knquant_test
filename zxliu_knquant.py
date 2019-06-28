# knquant笔试
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)


class Strategy_Halfday_reversal(object):
    def __init__(self, file_data='HS300 DATA.xlsx'):
        self.stock_hs300 = []  # 沪深300股票代码
        self.Data_hs300 = None  # 沪深300股票数据
        self._N = 30  # 每次持有股票数量
        self._compound = True
        self.Bench_Ret = None  # benchmark的收益率
        self.ReadData(file_data)
        self.Cal_Ret()
        self.Cal_Bench_Ret()

    # 可修改购买股票的数量
    @property
    def N(self):
        return self._N

    @N.setter
    def N(self, value):
        self._N = value

    # 可修改计算利息的方式：复利/单利
    @property
    def compound(self):
        return self._compound

    @compound.setter
    def compound(self, value):
        self._compound = value

    # 读取HS300 DATA数据
    def ReadData(self, file_data):
        Data = pd.read_excel(file_data)
        Data_hs300_tmp = []
        for i in range(math.ceil(Data.shape[1] / 4)):
            stock = Data.iloc[0, 4 * i + 1]
            self.stock_hs300.append(stock)
            stock_data = Data.iloc[4:, 4 * i:4 * i + 3]
            stock_data.columns = Data.iloc[2, 4 * i:4 * i + 3]
            stock_data.set_index('Date', inplace=True)
            stock_data.columns = pd.MultiIndex.from_product([[stock], Data.iloc[2, 4 * i + 1:4 * i + 3]])
            Data_hs300_tmp.append(stock_data)
        self.Data_hs300 = pd.concat(Data_hs300_tmp, axis=1)
        return None

    # 计算close-to-close,open-to-close和close-to-open收益率
    def Cal_Ret(self):
        for stock in self.stock_hs300:
            self.Data_hs300.loc[:, (stock, 'Ret_CO')] = self.Data_hs300.loc[:, (stock, 'close')] / self.Data_hs300.loc[:, (stock, 'open')] - 1
            self.Data_hs300.loc[:, (stock, 'Ret_OC')] = self.Data_hs300.loc[:, (stock, 'open')] / self.Data_hs300.loc[:, (stock, 'close')].shift(1) - 1
            self.Data_hs300.loc[:, (stock, 'Ret_CC')] = self.Data_hs300.loc[:, (stock, 'close')] / self.Data_hs300.loc[:, (stock, 'close')].shift(1) - 1
        return None

    # 计算根据close-to-open收益率,持有期为night策略的每日收益率
    def Strategy_CO(self):
        Strategy_CO_ret = pd.DataFrame(index=self.Data_hs300.index[1:-1], columns=['Strategy_CO_Ret'], dtype=np.float64)
        for i in range(len(self.Data_hs300) - 2):
            date = self.Data_hs300.index[i]
            Ret_CO_tmp = self.Data_hs300.loc[date, (slice(None), 'Ret_CO')]
            # 持有close-to-open收益率最低的N只股票
            Holding_Stock = Ret_CO_tmp.sort_values(ascending=True).iloc[:self._N].reset_index().level_0
            holding_date = self.Data_hs300.index[i + 1]
            Strategy_CO_ret.iloc[i] = self.Data_hs300.loc[holding_date, (Holding_Stock, 'Ret_OC')].mean()
        return Strategy_CO_ret

    # 计算根据open-to-close收益率,持有期为day策略的每日收益率
    def Strategy_OC(self):
        Strategy_OC_ret = pd.DataFrame(index=self.Data_hs300.index[1:-1], columns=['Strategy_OC_Ret'], dtype=np.float64)
        for i in range(len(self.Data_hs300) - 2):
            date = self.Data_hs300.index[i + 1]
            Ret_OC_tmp = self.Data_hs300.loc[date, (slice(None), 'Ret_OC')]
            # 持有close-to-open收益率最低的N只股票
            Holding_Stock = Ret_OC_tmp.sort_values(ascending=True).iloc[:self._N].reset_index().level_0
            holding_date = date
            Strategy_OC_ret.iloc[i] = self.Data_hs300.loc[holding_date, (Holding_Stock, 'Ret_CO')].mean()
        return Strategy_OC_ret

    # 计算最大回撤率和最大回撤期
    def Max_Drawdown(self, Ret_cum):
        Drawdown = Ret_cum / Ret_cum.cummax()
        max_drawdown = Drawdown.min() - 1
        drawdown_end = Drawdown.idxmin()
        drawdown_begin = Ret_cum.loc[:drawdown_end].idxmax()
        return (max_drawdown, drawdown_begin, drawdown_end)

    # 策略评价,包括计算总收益率,年化收益率,收益率方差,夏普比率,最大回撤率,最大回撤期,画累计收益
    def Strategy_Evaluate(self, name, Ret, plot_bench=False, bench_name='Bench_Ret_OC', save_fig=False):
        # Ret为2年的收益率Series,plot_bench=True画出benchmark的收益率曲线,compound=True计算复利
        Result = pd.DataFrame(index=[name])
        Result['begin date'] = Ret.index[0]
        Result['end date'] = Ret.index[-1]
        if self._compound:
            Ret_cum = (Ret + 1).cumprod()
            Result['annual return'] = Ret_cum.iloc[-1]**0.5 - 1
        else:
            Ret_cum = Ret.cumsum() + 1
            Result['annual return'] = Ret_cum.iloc[-1] / 2 - 1
        Result['total return'] = Ret_cum.iloc[-1] - 1
        Result['daily return std'] = Ret.std()
        Result['mean/std of daily return'] = Ret.mean() / Ret.std()
        Drawdown_info = self.Max_Drawdown(Ret_cum)
        Result['Max Drawdown'] = Drawdown_info[0]
        Result['Max Drawdown begin'] = Drawdown_info[1]
        Result['Max Drawdown end'] = Drawdown_info[2]
        # 绘图
        plt.figure(figsize=(12, 6))
        x = Ret_cum.index
        ret_cum = Ret_cum.values
        plt.plot(ret_cum, linewidth=2, linestyle='-', label=name)
        if plot_bench:
            if self._compound:
                bench_cc = (self.Bench_Ret['Bench_Ret_CC'] + 1).cumprod().values
                bench = (self.Bench_Ret[bench_name] + 1).cumprod().values
            else:
                bench_cc = (self.Bench_Ret['Bench_Ret_CC'].cumsum() + 1).values
                bench = (self.Bench_Ret[bench_name].cumsum() + 1).values
            plt.plot(bench_cc, linewidth=2, linestyle='-', label='Bench_Ret_CC')
            plt.plot(bench, linewidth=2, linestyle='-', label=bench_name)
        plt.legend(loc=0)
        plt.xlim(-1, len(x) + 1)
        x_tick = range(0, len(x), 40)
        x_label = [x[i].strftime('%Y-%m-%d') for i in x_tick]
        plt.xticks(x_tick, x_label, rotation=30)
        plt.title(name)
        if save_fig:
            plt.savefig(name + '.png')
        else:
            plt.show()
        return Result

    # 将所有股票简单平均加权作为benchmark,计算benchmark的收益率
    def Cal_Bench_Ret(self):
        Bench_Ret = pd.DataFrame(index=self.Data_hs300.index[1:-2], columns=['Bench_Ret_CC', 'Bench_Ret_CO', 'Bench_Ret_OC'], dtype=np.float64)
        for date in self.Data_hs300.index[1:-2]:
            Bench_Ret.loc[date, 'Bench_Ret_CC'] = self.Data_hs300.loc[date, (slice(None), 'Ret_CC')].mean()
            Bench_Ret.loc[date, 'Bench_Ret_CO'] = self.Data_hs300.loc[date, (slice(None), 'Ret_CO')].mean()
            Bench_Ret.loc[date, 'Bench_Ret_OC'] = self.Data_hs300.loc[date, (slice(None), 'Ret_OC')].mean()
        self.Bench_Ret = Bench_Ret
        return None

    def plot_Bench_Ret(self, save_fig=False):
        if self._compound:
            (self.Bench_Ret + 1).cumprod().plot(figsize=(12, 6))
        else:
            (self.Bench_Ret.cumsum() + 1).plot(figsize=(12, 6))
        plt.title('Benchmark Return')
        plt.ylabel('Cumulative Return')
        if save_fig:
            plt.savefig('Bench_Ret.png')
        else:
            plt.show()
        return None

    # 因子评价,包括计算IC,IR,分组收益率
    def Factor_Evaluate(self, factor_name, ret_name, lay=0, group=10, title_name=None, save_fig=False):
        IC_df = pd.DataFrame(index=self.Data_hs300.index[1:-1], columns=['IC', 'RankIC'], dtype=np.float64)
        GroupRet = pd.DataFrame(index=self.Data_hs300.index[1:-1], columns=['group' + str(j + 1) for j in range(group)], dtype=np.float64)
        for i in range(len(self.Data_hs300) - 2):
            holding_date = self.Data_hs300.index[i + 1]
            date = self.Data_hs300.index[i + 1 - lay]
            factor_tmp = self.Data_hs300.loc[date, (slice(None), factor_name)].reset_index(level=1, drop=True).astype(np.float64)
            factor_tmp.name = 'factor'
            ret_tmp = self.Data_hs300.loc[holding_date, (slice(None), ret_name)].reset_index(level=1, drop=True).astype(np.float64)
            ret_tmp.name = 'ret'
            IC_df.loc[holding_date, 'IC'] = factor_tmp.corr(ret_tmp, method='pearson')
            IC_df.loc[holding_date, 'RankIC'] = factor_tmp.corr(ret_tmp, method='spearman')
            tmp = pd.concat([factor_tmp, ret_tmp], axis=1).dropna()
            tmp['factor_rank'] = tmp['factor'].rank(pct=True)
            for j in range(group):
                GroupRet.loc[holding_date, 'group' + str(j + 1)] = tmp[(tmp['factor_rank'] > j / group) & (tmp['factor_rank'] < (j + 1) / group)]['ret'].mean()
        ICIR_df = pd.DataFrame(index=['IC', 'RankIC'], columns=['mean', '<0 per cent', 'IR'])
        ICIR_df['mean'] = IC_df.mean()
        ICIR_df['<0 per cent'] = (IC_df < 0).sum() / len(IC_df)
        ICIR_df['IR'] = IC_df.mean() / IC_df.std()
        self.GroupRet_plot(GroupRet, title_name, save_fig)
        return (ICIR_df, GroupRet)

    # 画分组累积收益率图
    def GroupRet_plot(self, GroupRet, title_name=None, save_fig=False):
        if self._compound:
            (GroupRet + 1).cumprod().plot()
        else:
            (GroupRet.cumsum() + 1).plot()
        if title_name is None:
            plt.show()
        else:
            plt.title(title_name)
            if save_fig:
                plt.savefig(title_name + '.png')
            else:
                plt.show()
        return None


if __name__ == '__main__':
    S = Strategy_Halfday_reversal()
    # 画出benchmark收益率曲线
    S.plot_Bench_Ret(save_fig=True)
    # 评价Strategy_CO
    Ret_CO = S.Strategy_CO()
    Result_CO = S.Strategy_Evaluate(name='Strategy_CO', Ret=Ret_CO.Strategy_CO_Ret, plot_bench=True, save_fig=True)
    Result_CO.to_csv('Strategy_CO_Result.csv')
    _ = S.Strategy_Evaluate(name='Strategy_CO - bench', Ret=Ret_CO.Strategy_CO_Ret - S.Bench_Ret.Bench_Ret_OC, save_fig=True)
    ICIR_CO, _ = S.Factor_Evaluate(factor_name='Ret_CO', ret_name='Ret_OC', lay=1, group=5,
                                   title_name='Strategy_CO_5Group', save_fig=True)
    ICIR_CO.to_csv('Strategy_CO_IC.csv')
    _, _ = S.Factor_Evaluate(factor_name='Ret_CO', ret_name='Ret_OC', lay=1, group=10,
                             title_name='Strategy_CO_10Group', save_fig=True)
    # 评价Strategy_OC
    Ret_OC = S.Strategy_OC()
    Result_OC = S.Strategy_Evaluate(name='Strategy_OC', Ret=Ret_OC.Strategy_OC_Ret, plot_bench=True,
                                    bench_name='Bench_Ret_CO', save_fig=True)
    Result_OC.to_csv('Strategy_OC_Result.csv')
    _ = S.Strategy_Evaluate(name='Strategy_OC - bench', Ret=Ret_OC.Strategy_OC_Ret - S.Bench_Ret.Bench_Ret_CO, save_fig=True)
    ICIR_OC, _ = S.Factor_Evaluate(factor_name='Ret_OC', ret_name='Ret_CO', lay=0, group=5,
                                   title_name='Strategy_OC_5Group', save_fig=True)
    ICIR_OC.to_csv('Strategy_OC_IC.csv')
    _, _ = S.Factor_Evaluate(factor_name='Ret_OC', ret_name='Ret_CO', lay=0, group=10,
                             title_name='Strategy_OC_10Group', save_fig=True)
