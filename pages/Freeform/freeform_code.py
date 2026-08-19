#This is code from the AstroTech software analysisoutlines. I did not create it myself, but wanted to include it as a resource for a freeform spectrometer.

# connect with Google Drive

from google.colab import drive

# this statement will ask for your permission to access your files in Google Drive.
drive.mount('/content/drive')

# module imports

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from astropy.io import fits
from astropy.modeling import models, fitting
import warnings
import glob
from scipy.ndimage import rotate


# write paths
mainpath = '/content/drive/Shareddrives/AstroTech 2026 Participant Shared Drive/BROSKI/'
darks_path = mainpath + 'median_dark1.fits'
flats_path = mainpath + 'median_flat1.fits'

os.listdir(mainpath)




def plot_image(data, x_label, y_label, title, colorbar='Detector Counts'):
  '''
  ADD DOCSTRING
  '''
  print(title, "Data:")
  print(data)
  print(title, "Shape:")
  print(data.shape)

  plt.imshow(data, origin='lower', cmap='viridis')
  plt.xlabel(x_label)
  plt.ylabel(y_label)
  plt.title(title)

  plt.colorbar(label=colorbar)

def plot_spectrum(data, x_label, y_label, collapse=False):
  '''
  ADD DOCSTRING
  '''
  if collapse:
    data = np.sum(data, axis=0)

  # inspect 1D spectrum
  print("1D Spectral Data:")
  print(data)
  print("1D Spectral Shape:")
  print(data.shape)

  # Plot 1D spectrum
  print("1D Spectrum:")
  x_length = len(data)
  x_pixel_coordinates = np.array(range(0, x_length, 1))
  plt.plot(x_pixel_coordinates, data)
  plt.xlabel(x_label)
  plt.ylabel(y_label)
  plt.show()

  return data, x_length, x_pixel_coordinates

def read_fits_file(fits_file):
    """
    Function to read in the data from a simple fits file.

    Args:
        fits_file (str): The path to the fits file

    Returns:
        np.array: The data from the fits file
    """
    fits_file_hdul = fits.open(fits_file)

    data = fits_file_hdul[1].data

    return data

def apply_linear_wavelenth_soln(x_coord, slope, intercept):
    """
    Convert x pixel coordinate to wavelength in nm.

    Args:
        x_coord (np.array): x-coordinate of the detector
        slope (float): Slope of wavelength solution
        intercept (float): Intercept of wavelength solution

    Returns:
        np.array: wavelength coordinate of the spectrum
    """
    return x_coord * slope + intercept



#### EDIT

slope = 0
y_intercept = 0

image_filename = 'test_tint100000_coadd1.fits'

Helium = True
Argon = False
Sulfur = False
Hydrogen = False

####

full_path = mainpath + 'Raw Images/' + image_filename
print(full_path)

raw_image_data = read_fits_file(full_path)
median_dark = read_fits_file(darks_path)
median_flat = read_fits_file(flats_path)




# Let's inspect the data...
print("Image Data:")
print(raw_image_data)
print("Raw Spectrum Image Shape:")
print(raw_image_data.shape)

plot_image(raw_image_data, 'Pixel Coordinate', 'Counts', 'Raw Data')

calibrated_data = (raw_image_data - median_dark) / median_flat

plot_image(calibrated_data, 'Pixel Coordinate', 'Counts', 'Calibrated Data')



#if spectrum is not vertical
rotated_image = rotate(calibrated_data, angle=-8, reshape=False, mode="constant", cval=0)

plot_image(rotated_image, 'x', 'y', 'rotate')

cropped_spectrum = rotated_image[200:1700, 700:2800]

plot_image(cropped_spectrum, 'x', 'y', 'rotate')


calibrated_spectrum, x_length, x_pixel_coordinates = plot_spectrum(cropped_spectrum, 'Detector X Pixel Location', 'Detector Counts', collapse=True)


# Let's plot the wavelength-calibrated spectrum!
print("Wavelength-calibrated Spectrum:")
wl_coordinates = apply_linear_wavelenth_soln(
    x_coord=np.array(x_pixel_coordinates),
    slope=slope,
    intercept=intercept
)
plt.plot(wl_coordinates, calibrated_spectrum)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Calibrated Detector Counts')
plt.show()