"""
Fixed income instruments

This file is part of FBox.

Copyright (c) 2014, Pedro A.C. Tavares
All rights reserved.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this program.  If not, see <http://www.gnu.org/licenses/>
"""

from datetime import datetime,date
from numpy import array,ones
from scipy.optimize import fmin_powell
from scipy.interpolate import interp1d
import dates



class cash(object):
    """
    Cash instrument
    
    Properties:
      start_date      Start date of deposit or loan (datetime.datetime, datetime.date or equivalent)
      maturity_date   Redemption date of deposit or loan (datetime.datetime, datetime.date or equivalent)
      notional        Notional amount (int, float)
      rate            Interest rate (float)
      day_count       Day count convention (string)
    
    Methods:
      par_rate        Par interest rate
      value           Net present value
    """

    def __init__(self,start,maturity,notional,rate,dcc):
        self.start_date = start
        self.maturity_date = maturity
        self.notional = notional
        self.rate = rate
        self.day_count = dcc
        
        self.yf = dates.year_fraction(self.start_date,self.maturity_date,self.day_count)
        
    def par_rate(self,yc):
        r = ( yc(self.start_date) / yc(self.maturity_date) - 1.0 ) / self.yf
        return r

    def value(self,yc):
        pv = self.notional * ( (1. + self.rate * self.yf) * yc(self.maturity_date) - yc(self.start_date) )
        return pv
    


class simple_swap(object):
    """
    Swap
    
    Properties:
      schedule        Schedule of dates (iterable of datetime or equivalent)
      notional        Notional amount (int, float)
      rate            Interest rate (float)
    
    Methods:
      par_rate        Par interest rate
      value           Net present value
    """

    def __init__(self,schedule,notional,rate):
        self.schedule = schedule
        self.notional = notional
        self.rate = rate

        self.start_date = schedule.start_date
        self.maturity_date = schedule.maturity_date
                        
    def annuity(self,yc):                
        a = [yf * yc(t) for t,yf in zip(self.schedule.pay_dates,self.schedule.year_fractions)]
        return sum(a)

    def par_rate(self,yc):
        return self._b(yc) / self.annuity(yc)
    
    def value(self,yc):
        return self.notional * ( self._b(yc) - self.rate * self.annuity(yc) )
    
    def _b(self,yc):
        if self.start_date > yc.date:
            return yc(self.start_date) - yc(self.maturity_date)
        else:
            return 1.0 - yc(self.maturity_date)
            


#---------------------------------------------------------------------------

import unittest

class testyc(object):
    date = datetime(2013,4,1)
    def __call__(self,t):
        return 1.0


class __test_swap__(unittest.TestCase):

#    def setUp(self):
#        pass

    def test_cash(self):
        yc = testyc()
        t0 = yc.date

        c = cash(t0,t0+dates.relativedelta(days=30),1.0,0.01,'A/360')
        r = c.par_rate(yc)
        c.rate = r
        v = c.value(yc)

        self.assertAlmostEqual(v,0.0,3) 
        
    def test_swap(self):
        yc = testyc()
        t0 = datetime(2014,4,1)

        s = simple_swap(dates.schedule(t0,t0+dates.relativedelta(years=3),6,False,'A/360'),1.0,0.1)
        r = s.par_rate(yc)
        s.rate = r
        v = s.value(yc)

        self.assertAlmostEqual(v,0.0,3) 

