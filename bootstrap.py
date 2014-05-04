"""
Yield curve bootstrapping

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
import dates,fixed_income

    
class yield_curve(interp1d):
    date = None
    
    def __call__(self,t):
        if isinstance(t,(date,datetime)): t = t.toordinal()
        return float( super(yield_curve,self).__call__(t) )
    

class __fmin__(object):
    def __init__(self,date,instruments,interpolation,debug):
        self.inst = instruments
        self.date = date
        self.interpolation = interpolation
        self.debug = debug
        
        self.fixings = array( [date.toordinal()] + [inst.maturity_date.toordinal() for inst in instruments] )
        self.discounts = ones( len(self.fixings) )
        self.df = None
        
    def __call__(self,discounts):
        self.discounts[1:] = discounts # may be faster than appending '1' to the discounts array
        self.df = yield_curve(self.fixings,self.discounts,kind=self.interpolation)
        self.df.date = self.date
        err = sum( [i.value(self.df)**2 for i in self.inst] )
        if self.debug: print '>>> Bootstrap iteration:',err,discounts
        return err
   

        
def bootstrap(date,instruments,interpolation='linear',debug=False):
    func = __fmin__(date,instruments,interpolation,debug)
    fmin_powell(func,ones(len(func.fixings)-1),disp=False)
    return func.df


#---------------------------------------------------------------------------

import unittest

class __test_bootstrap__(unittest.TestCase):

#    def setUp(self):
#        pass

    def test_simple(self):
        t0 = datetime(2014,4,1)
        
        cash = [ 
            fixed_income.cash(t0,t0+dates.relativedelta(days=t),1.0,r,'A/360')
            for t,r in ((30,0.005),(90,0.007),(180,0.010))
        ]
        
        swaps = [
            fixed_income.simple_swap(dates.schedule(t0,t0+dates.relativedelta(years=t),6,False,'A/360'),1.0,r)
            for t,r in ((1,0.012),(3,0.02),(5,0.020)) 
        ]
        
        inst = cash + swaps
        
        func = __fmin__(t0,inst,'linear',True)
        func( ones(len(inst)) )
        
        yc = bootstrap(t0,inst)
        print '>>> Discounts:',[yc(i.maturity_date) for i in inst]
        
        
        for i in inst:
            self.assertAlmostEqual(i.par_rate(yc),i.rate,3) 
            self.assertAlmostEqual(i.value(yc),0.0,3) 

