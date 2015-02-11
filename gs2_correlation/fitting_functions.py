############################
# gs2_correlation_analysis #
#    Ferdinand van Wyk     #
############################

###############################################################################
# This file is part of gs2_correlation_analysis.
#
# gs2_correlation_analysis is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gs2_correlation_analysis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gs2_correlation_analysis.  
# If not, see <http://www.gnu.org/licenses/>.
###############################################################################

# This file contains various fitting functions called during the main 
# correlation analysis

import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt
import scipy.signal as sig

###########################
# Model Fitting Functions #
###########################

#Model function to be fitted to data, as defined in Anthony's papers
def tilted_gauss(xdata_tuple, lx, ly, kx, ky):
    (x,y) = xdata_tuple
    exp_term = np.exp(- (x/lx)**2 - (y/ly)**2 )
    cos_term = np.cos(kx*x + ky*y)
    fit_fn =  exp_term*cos_term
    # fitting function only works on 1D data, reshape later to plot
    return fit_fn.ravel()

#Decaying exponential for time correlation with positive flow
def decaying_exp(t, tau_c):
    exp_fn = np.exp(- abs(t) / tau_c)
    # fitting function only works on 1D data, reshape later to plot
    return exp_fn.ravel() 

#Growing exponential for time correlation with negative flow
def growing_exp(t, tau_c):
    exp_fn = np.exp(t / tau_c)
    # fitting function only works on 1D data, reshape later to plot
    return exp_fn.ravel()

#Growing exponential for time correlation with negative flow
def osc_exp(t, tau_c, omega):
    fit_fn = np.exp(- (t / tau_c)**2) * np.cos(omega * t)
    # fitting function only works on 1D data, reshape later to plot
    return fit_fn.ravel() 

###################
# Misc Procedures #
###################

# Function which checks monotonicity. Returns True or False.
def strictly_increasing(L):
    return all(x<y for x, y in zip(L, L[1:]))
