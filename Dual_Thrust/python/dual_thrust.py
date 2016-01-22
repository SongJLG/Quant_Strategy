# -*- coding: utf-8 -*-
from gmsdk.api import StrategyBase
from gmsdk import md
from gmsdk.enums import *
import arrow
import time

#每次开仓量
OPEN_VOL = 5

class Dual_Thrust(StrategyBase)
    def __init__(self, *args, **kwargs):
        super(Dual_Thrust, self).__init__(*args, **kwargs)
        #上下界
        self.up = None
        self.dw = None
        
        #开仓标识
        self.open_long_flag = False
        self.open_short_flag = False
                
        #持仓量
        self.holding = 0
        
        self.__get_param()
        self.__init_data()
        
     def __get_param( self ):
        '''
        获取配置参数
        '''
        #交易标的
        
        self.trade_symbol = self.config.get('para', 'trade_symbol')
        pos = self.trade_symbol.find('.')
        self.exchange = self.trade_symbol[:pos]
        self.sec_id = self.trade_symbol[pos+1:]

        FMT = '%s %s'
        today = arrow.now().date()
        
        #首根K线
        first_kline_time = self.config.get('para', 'first_kline_time')
        et = FMT % (today.isoformat(), first_kline_time)
        self.first_kline_time_str = et
        
        #平仓时间
        end_time = self.config.get('para', 'end_time')
        et = FMT % (today.isoformat(), end_time)
        self.end_trading = arrow.get(et).replace(tzinfo='local').timestamp
        print "end time %s" % (et)
        
        self.Day = self.config.get('para', 'Day')
        self.k1 = self.config.get('para', 'k1')
        self.k2 = self.config.get('para', 'k2')
        
    def __init_data( self ):
        High_Price = []
        Close_Price = []
        Low_Price = []
        
        dailybars = self.get_last_n_dailybars( self.trade_symbol, self.Day)
        
        if len(dailybars) > 0 :
            for i in range(0, self.Day):
                High_Price.append(dailybars[i].high)
                Close_Price.append(dailybars[i].close)    
                Low_Price.append(dailybars[i].low)
        
         HH_Price = max(High_Price)     #最高价的最高价       
         HC_Price = max(Close_Price)    #收盘价的最高价
         LC_Price = min(Close_Price)    #收盘价的最低价                
         LL_Price = min(Low_Price)      #最高价的最高价 
         Range = max(HH_Price - LC_Price, HC_Price - LL_Price)
                                 
        #第一根K线数据
         while self.up is None or self.dw is None:
            print 'waiting for get the first K line...'
            bars = self.get_bars( self.trade_symbol, 60, self.first_kline_time_str, self.first_kline_time_str )
            if  len(bars) > 0 :
                self.up = bars[0].open + self.k1*Range   #上轨
                self.dw = bars[0].open - self.k2*Range   #下轨
                print 'up:%s, dw: %s'%(self.up, self.dw)

    def on_tick(self, tick):
        #tick报价
        self.close = tick.last_price
        
    def on_bar(self, bar):
        '''
        bar数据
        '''
        #判断开仓条件
        if self.close > self.up and 0 == self.holding :
            self.open_long(self.exchange, self.sec_id, 0, OPEN_VOL )
            self.holding += OPEN_VOL
            self.open_long_flag = True
            self.open_short_flag = False
            print 'open long: last price %s, vol %s'%(self.close, OPEN_VOL)
            
        elif self.close < self.dw and 0 == self.holding :
            self.open_short( self.exchange, self.sec_id, 0, OPEN_VOL )
            self.holding += OPEN_VOL
            self.open_long_flag = False
            self.open_short_flag = True
            print 'open short: last price %s, vol %s'%(self.close, OPEN_VOL)
            
         #止损退出
         
         if self.close < self.up*k1 and self.open_long_flag :
            self.close_long( self.exchange, self.sec_id, 0, self.holding )
            self.open_long_flag = False
            self.open_short_flag = False
            print 'close long: stop lost, vol: %s'%self.holding
            
         elif self.close > self.dw/k2 and self.open_short_flag :
            self.close_short( self.exchange, self.sec_id, 0, self.holding ) 
            self.open_long_flag = False
            self.open_short_flag = False
            print 'close long: stop lost, vol: %s'%self.holding   
            


        #日内平仓
        if bar.utc_time > self.end_trading :
        
            if self.open_long_flag :
                self.close_long( self.exchange, self.sec_id, 0, self.holding )
                print 'end trading time close long, vol: %s'%self.holding
                
            elif self.open_short_flag :
                self.close_short( self.exchange, self.sec_id, 0, self.holding ) 
                print 'end trading time close short, vol: %s'%self.holding

if __name__ == '__main__':
    DT = Dual_Thrust(config_file='Dual_Thrust.ini')
    ret = DT.run()
    print DT.get_strerror(ret)         
    