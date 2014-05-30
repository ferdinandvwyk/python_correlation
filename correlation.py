# This program reads in GS2 density fluctuation data in Fourier space, converts to real space
# and calculates the perpendicular correlation function using the Wiener-Kinchin theorem. 
# The program takes in a command line argument that specifies the GS2 NetCDF file that 
# contains the variable ntot(t, spec, ky, kx, theta, ri).
# Use as follows:
#
#     python correlation.py <time/perp analysis> <location of .nc file>

import os, sys
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt
import scipy.interpolate as interp
from scipy.io import netcdf
import fit
import film

# Read command line argument specifying location of NetCDF file
analysis =  str(sys.argv[1]) #specify analysis (time or perp)
if analysis != 'perp' and analysis != 'time':
  raise Exception('Please specify analysis: time or perp.')
in_file =  str(sys.argv[2])

#########################
# Function Declarations #
#########################

# Function which converts from GS2 field to complex field which can be passed to fft routines
def real_to_complex(field):
  # convert fgs2 to numpy 2D real Fourier transform fr(x,y,theta)
  # nx,ny are number of points within a period
  # => periodic points are nx+1, ny+1 apart
  [nk1, nk2] = [ field.shape[0], field.shape[1]]
  n1 = nk1; n2 = (nk2-1)*2 #assuming second index is half complex
  cplx_field = np.empty([nk1,nk2],dtype=complex)
  cplx_field.real = field[:,:,0]
  cplx_field.imag = field[:,:,1]
  # fix fft normalisation that is appropriate for numpy fft package
  cplx_field = cplx_field*nx*ny/2
  return cplx_field

# Function which applies WK theorem to a real 2D field field(x,y,ri) where y is assumed to be
# half complex and 'ri' indicates the real/imaginary axis (0 real, 1 imag). 
# The output is the correlation function C(dx, dy).
def wk_thm(field):
# create complex field out of 
  c_field = real_to_complex(field)
  #The Wiener-Khinchin thm states that the autocorrelation function is the FFT of the power spectrum.
  #The power spectrum is defined as abs(A)**2 where A is a COMPLEX array. In this case f.
  c_field = np.abs(c_field**2)
  #option 's' below truncates by ny by 1 such that an odd number of y pts are output => need to have corr fn at (0,0)
  corr = np.fft.irfft2(c_field,axes=[0,1], s=[c_field.shape[0], 2*(c_field.shape[1]-1)-1]) #need to use irfft2 since the original signal is real in real space
  return corr

#Finally want to fit the 2D correlation function with a tilted Gaussian and extract the fitting parameters
def perp_fit(avg_corr, xpts, ypts):
  x,y = np.meshgrid(xpts, ypts)
  x = np.transpose(x); y = np.transpose(y)

  # lx, ly, ky, Th
  init_guess = (10.0, 10.0, 0.01, -0.3)
  popt, pcov = opt.curve_fit(fit.tilted_gauss, (x, y), avg_corr.ravel(), p0=init_guess)

  data_fitted = fit.tilted_gauss((x, y), *popt)

  plt.clf()
  #plt.contourf(xpts[49:79], ypts[21:40], np.transpose(avg_corr[49:79,21:40]))
  plt.contourf(xpts, ypts, np.transpose(avg_corr))
  plt.colorbar()
  plt.hold(True)
  #plt.contour(xpts[49:79], ypts[21:40], np.transpose(data_fitted.reshape(nx,ny-1)[49:79,21:40]), 8, colors='w')
  plt.contour(xpts, ypts, np.transpose(data_fitted.reshape(nx,ny-1)), 8, colors='w')
  plt.xlabel(r'$\Delta x (\rho_i)$')
  plt.ylabel(r'$\Delta y (\rho_i)$')
  plt.savefig('fit.eps')

  #Write the fitting parameters to a file
  # Order is: [lx, ly, ky, Theta]
  np.savetxt('fitting_parameters.csv', (popt, pcov.diagonal()), delimiter=',', fmt='%1.4e')

#############
# Main Code #
#############

ncfile = netcdf.netcdf_file(in_file, 'r')
density = ncfile.variables['ntot_t'][:,0,:,:,:,:] #index = (t, spec, ky, kx, theta, ri)
th = ncfile.variables['theta'][:]
kx = ncfile.variables['kx'][:]
ky = ncfile.variables['ky'][:]
t = ncfile.variables['t'][:]

#Start timer
t_start = time.clock()
#Ensure time is on a regular grid for uniformity
tnew = np.linspace(min(t), max(t), len(t))
shape = density.shape
ntot_reg = np.empty([shape[0], shape[2], shape[1], shape[3], shape[4]])
for i in range(shape[1]):
  for j in range(shape[2]):
    for k in range(shape[3]):
      for l in range(shape[4]):
        f = interp.interp1d(t, density[:, i, j, k, l])
        ntot_reg[:, j, i, k, l] = f(tnew) #perform a transpose here: ntot(t,kx,ky,theta,ri)

#Start timer
t_end = time.clock()
print 'Interpolation Time = ', t_end-t_start, ' s'

#Clear density from memory
density = None

#################
# Perp Analysis #
#################

if analysis == 'perp':
  # Perform inverse FFT to real space ntot[kx, ky, th]
  shape = ntot_reg.shape
  nt = shape[0]
  nx = shape[1]
  nky = shape[2]
  ny = (nky-1)*2
  nth = shape[3]
  corr_fn = np.empty([nt,nx,ny-1,nth],dtype=float)
  for it in range(0,nt):
    for ith in range(0,nth):
      corr_fn[it,:,:,ith] = wk_thm(ntot_reg[it,:,:,ith,:])

      #Shift the zeros to the middle of the domain (only in x and y directions)
      corr_fn[it,:,:,ith] = np.fft.fftshift(corr_fn[it,:,:,ith], axes=[0,1])
      #Normalize the correlation function
      corr_fn[it,:,:,ith] = corr_fn[it,:,:,ith]/np.max(corr_fn[it,:,:,ith])

  xpts = np.linspace(-2*np.pi/kx[1], 2*np.pi/kx[1], nx)
  ypts = np.linspace(-2*np.pi/ky[1], 2*np.pi/ky[1], ny-1)
  film.film_2d(xpts, ypts, corr_fn[:,:,:,10], 100, 'corr')

  # Calculate average correlation function over time at zero theta
  plt.clf()
  avg_corr = np.mean(corr_fn[:,:,:,10], axis=0)
  #plt.contourf(xpts[49:79], ypts[21:40], np.transpose(avg_corr[49:79,21:40]), 10)
  plt.contourf(xpts, ypts, np.transpose(avg_corr), 10)
  plt.colorbar()
  plt.xlabel(r'$\Delta x (\rho_i)$')
  plt.ylabel(r'$\Delta y (\rho_i)$')
  plt.savefig('averaged_correlation.eps')

  perp_fit(avg_corr, xpts, ypts)

#################
# Time Analysis #
#################
# The time correlation analysis involves looking at each radial location
# separately, and calculating C(dy, dt). Depending on whether there is significant
# flow, can fit a decaying exponential to either the central peak or the envelope
# of peaks of different dy's
elif analysis == 'time':
  # As given in Bendat & Piersol, need to pad time series with zeros to separate parts
  # of circular correlation function 
  shape = ntot_reg.shape
  nt = shape[0]
  nx = shape[1]
  nky = shape[2]
  ny = (nky-1)*2
  nth = shape[3]
  ntot_pad = np.empty([2*nt, nx, nky, nth, shape[4]])
  ntot_pad[:,:,:,:,:] = 0.0
  ntot_pad[0:shape[0],:,:,:,:] = ntot_reg

  # For each x value in the outboard midplane (theta=0) calculate the function C(dt,dy)
  corr_fn = np.empty([2*nt,nx,ny-1,nth],dtype=float)
  for ix in range(0,nx):
    for ith in range(0,nth):
      #Do correlation analysis but only keep first half as per B&P
      corr_fn[:,ix,:,ith] = wk_thm(ntot_pad[:,ix,:,ith,:])

      #Shift the zeros to the middle of the domain (only in t and y directions)
      corr_fn[:,ix,:,ith] = np.fft.fftshift(corr_fn[:,ix,:,ith], axes=[0,1])
      #Normalize the correlation function
      corr_fn[:,ix,:,ith] = corr_fn[:,ix,:,ith]/np.max(corr_fn[:,ix,:,ith])

  plt.plot(corr_fn[:,10,30,10])
  plt.show()















