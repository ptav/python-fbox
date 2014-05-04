"""
Date utilities

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
from dateutil.relativedelta import relativedelta
from functools import partial

#---------------------------------------------------------------------------
# Dates
#---------------------------------------------------------------------------

def add_days(start,days):
    """Add given number of days to a date"""
    return start + relativedelta(days = days)
    

def add_months(start,months):
    """Add given number of months to a date"""
    return start + relativedelta(months = months)
    

def add_years(start,years):
    """Add given number of years to a date"""
    return start + relativedelta(years = years)
    
    
"""Return year fraction for 30/360 and Act/N conventions"""
def year_fraction(start,end,dcc):
    if dcc == "30/360":
        return 30 * (end.month - start.month) / 360
    elif type(dcc) == type('a') and (dcc[0] == 'A' or dcc[0] == 'a'):
        c = float(dcc[-3:])
        return (end - start).days / c
    else:
        return (end - start).days / dcc


def tenor_to_date(tenor,date):
    if tenor[-1] == 'd':
        return date + relativedelta(days = int(tenor[:-1]))

    elif tenor[-1] == 'm':
        return date + relativedelta(months = int(tenor[:-1]))

    elif tenor[-1] == 'y':
        return date + relativedelta(years = int(tenor[:-1]))

    else:
        raise RuntimeError('Invalid tenor ' + tenor)


    
class schedule(object):
    """
    Dates schedule
    
    Properties:
      start_date      Start date of deposit or loan (datetime.datetime, datetime.date or equivalent)
      maturity_date   Redemption date of deposit or loan (string, datetime.datetime, datetime.date or equivalent)
      period          Coupon period (string)
      short_stub      True if first coupon is short (bool)
      day_count       If a day count convention is given year-fraction will be computed (string or None)
    
      full            Full dates schedule data
      pay_dates       List of payment dates
      set_dates       List of set date
    """
    
    def __init__(self,start,maturity,period,short_stub=True,day_count=None):
        self.start_date = start
        self.maturity_date = tenor_to_date(maturity,start) if isinstance(period,basestring) else maturity
        self.period = period if isinstance(period,basestring) else str(period) + 'm'
        self.short_stub = short_stub
        self.day_count = day_count
        
        self._set_schedule()


    def _set_schedule(self):
        p = '-' + self.period
            
        s = []
        t = self.maturity_date
        while t >= self.start_date:
            s.insert(0,t)
            t = tenor_to_date(p,t)

        if self.short_stub and s[0] != self.start_date: s.insert(0,self.start_date)
        else: s[0] = self.start_date
    
        self.start_dates = s[:-1]
        self.pay_dates = self.end_dates = s[1:]
        
        self.full = [self.start_dates,self.end_dates,self.pay_dates]
                
        if self.day_count != None:
            self.year_fractions = [year_fraction(t0,t1,self.day_count) for t0,t1 in zip(self.start_dates,self.end_dates)]
            self.full.append(self.year_fractions)
        else:
            self.year_fractions = None

        
#---------------------------------------------------------------------------

import unittest

class __test_dates__(unittest.TestCase):

#    def setUp(self):
#        pass

    def test_schedule(self):
        t0 = datetime(2014,4,1)
        t1 = datetime(2016,12,1)
        
        x = schedule(t0,t1,6,day_count='A/360')
        y = [
             datetime(2014,4,1),datetime(2014,6,1),datetime(2014,12,1),
             datetime(2015,6,1),datetime(2015,12,1),
             datetime(2016,6,1),datetime(2016,12,1),
        ]
        self.assertEqual(x.start_dates,y[:-1]) 
        self.assertEqual(x.end_dates,y[1:]) 
        self.assertEqual(x.pay_dates,y[1:]) 

        x = schedule(t0,t1,6,short_stub=False)
        y = y[0:1] + y[2:]
        self.assertEqual(x.start_dates,y[:-1]) 
        self.assertEqual(x.end_dates,y[1:]) 
        self.assertEqual(x.pay_dates,y[1:]) 

