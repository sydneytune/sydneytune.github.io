#Note: This code did not have a reboot function. If the camera or another component gets unplugged, the code will just stop itself. Check out the DIY Spectrometer code for reboot examples.
#This is code for a Raspberry Pi 4 with a ZWO ASI camera. It works best for linux.

#imports
import zwoasi as asi
import numpy as np
import imageio
import sys
import os
import datetime
import time
import astropy
from astropy.io import fits
import shutil
from datetime import datetime

#definitions for file names
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"/home/spase/script_started_{timestamp}.txt"

#information about the script start time
with open(filename, 'w') as f:
    f.write(f"Script started at {datetime.now()}.\n")

# Initialize SDK
sdk_path = '/home/spase/Downloads/ASI_Camera_SDK/asi_linux/ASI_linux_mac_SDK_V1.38/lib/armv8/libASICamera2.so'

asi.init(sdk_path)

# Check for camera
if asi.get_num_cameras() == 0:
    print("No cameras found.")
    sys.exit(1)

camera_names = asi.list_cameras()
print(f"Found camera: {camera_names[0]}")

# Open camera
camera = asi.Camera(0)
camera_info = camera.get_camera_property()

# Set image format and ROI (full frame, binning 1x1)
width, height = camera_info['MaxWidth'], camera_info['MaxHeight']
camera.set_roi_format(width, height, 1, asi.ASI_IMG_RAW16)    #this uses 16-bit photos

# Set USB bandwidth
camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, 80)

# Initial settings
#Auto-exposure didn't work well for our photos. We coded in our own instead
exposure = 600000  # µs
gain = 800
max_attempts = 8
target_mean = 37500
lower_bound = 30000
upper_bound = 45000

#change this to where you want the photos saved
path = 'home/spase/Pictures/test_images'
output_folder = '/home/spase/Pictures/test_images'

#will stop the code if there is not enough disk space
def has_enough_disk_space(path, min_required_mb=50):

    total, used, free = shutil.disk_usage(path)
    metric = free // (1024 * 1024) >= min_required_mb
    return metric

#writes a header to keep track of the camera settings
def generate_header():
    hdr = fits.Header()
    hdr['EXPTIME'] = exposure / 1e6  # µs to seconds
    hdr['GAIN'] = gain
    hdr['DATE-OBS'] = datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    hdr['CAMERA'] = camera_info['Name']
    hdr['MAXWID'] = camera_info['MaxWidth']
    hdr['MAXHEIT'] = camera_info['MaxHeight']

    #get temp if possible
    try:
        temperature = camera.get_control_value(asi.ASI_TEMPERATURE)[0] / 10
        hdr['CCDTEMP'] = temperature
    except Exception:
        hdr['CCDTEMP'] = 'UNKNOWN'
    return hdr

#we use the mean value to figure out the exposure and gain
#this takes a strip out to use since our spectra didn't fill up the whole image
def calculate_clean_mean(image, crop_rows=20):
    return np.mean(image[:-crop_rows])  # Remove bottom rows with artifacts

# Main capture loop
while True:
    if os.path.exists("/home/spase/stop_script.txt"):
        with open('/home/spase/script_stopped.txt', 'w') as f:
            f.write(f"Script stopped at {datetime.now()}.\n")
        break

    if not has_enough_disk_space(output_folder):
        print("Low disk space. Exiting.")    #important to know why the code stopped
        break

    #turn off the auto gain
    camera.set_control_value(asi.ASI_GAIN, gain, auto=False)
    start_time = time.time()

    #turn off the auto exposure
    for attempt in range(max_attempts):
        camera.set_control_value(asi.ASI_EXPOSURE, exposure, auto=False)
        image = camera.capture()
        mean_val = calculate_clean_mean(image)
        print(f"Attempt {attempt + 1}: mean = {mean_val:.2f}, exposure = {exposure}, gain = {gain}")

    #manual "auto exposure" loop
        # Good image
        if lower_bound <= mean_val <= upper_bound:
            print("Mean within range. Saving image.")
            break

        # Too dark
        elif mean_val < lower_bound:
            if exposure >= 15000000:
                print("Exposure maxed, increasing gain.")
                gain = 600  # Max gain
                camera.set_control_value(asi.ASI_GAIN, gain, auto=False)
                image = camera.capture()
                mean_val = calculate_clean_mean(image)
                if mean_val < lower_bound:
                    print("Still too dark after max gain. Skipping.")
                    break
            else:
                scale_factor = target_mean / mean_val
                exposure = int(exposure * scale_factor)
                exposure = min(exposure, 15000000)

        # Too bright
        elif mean_val > upper_bound:
            if exposure <= 100:
                print("Exposure at minimum, lowering gain.")
                gain = 0  # Min gain
                camera.set_control_value(asi.ASI_GAIN, gain, auto=False)
                image = camera.capture()
                mean_val = calculate_clean_mean(image)
                if mean_val > upper_bound:
                    print("Still too bright after reducing gain. Skipping.")
                    break
            else:
                scale_factor = target_mean / mean_val
                exposure = int(exposure * scale_factor)
                exposure = max(exposure, 100)

    # Save image
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_path = os.path.join(output_folder, f'zwoasi_capture_{timestamp}.fits')
    text_path = os.path.join(output_folder, f'zwoasi_capture_{timestamp}.txt')

    header = generate_header()
    fits.writeto(image_path, image, header=header, overwrite=True)

    with open(text_path, 'w') as f:
        f.write(f"Mean: {mean_val:.2f}\nExposure: {exposure}\nGain: {gain}\nTime stamp: {timestamp}")

    print(f"Image saved: {image_path}")

    # Wait for next interval
    elapsed_time = time.time() - start_time
    sleep_time = max(0, 20 - elapsed_time)
    print(f"Waiting {sleep_time:.2f} seconds...\n")
    time.sleep(sleep_time)


