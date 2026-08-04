import warnings
warnings.filterwarnings("ignore")

import os

os.environ["GENICAM_GENTL64_PATH"] = "/home/rockntrolls/Downloads/VimbaX_2026-1/cti"
os.environ["LD_LIBRARY_PATH"] = "/home/rockntrolls/Downloads/VimbaX_2026-1/api/lib"

import time
import datetime
import numpy as np
import imageio.v3 as iio
import shutil

from vmbpy import *
from astropy.io import fits
from smbus2 import SMBus
import sys
import subprocess

from conditions_sensor import *

TARGET_MEAN = 800
LOWER_BOUND = 400
UPPER_BOUND = 1600


MAX_EXPOSURE = 849053.826
MIN_EXPOSURE = 12.957

MAX_GAIN = 21.0
MIN_GAIN = 0.0
sensor = DFRobot_Environmental_Sensor_I2C(1, DEV_ADDRESS)

if sensor.begin():
    print("Environmental sensor initialized")
else:
    print("Environmental sensor not found")
    
    
def low_storage(threshold_gb=1):
    total, used, free = shutil.disk_usage("/")
    free_gb = free / (1024**3)
    return free_gb < threshold_gb


frame_count = 0
last_save_time = 0

#ambient sensor
I2C_ADDR = 0x22
bus = SMBus(1)

def read_ambient():
    try:
        temp = sensor.get_temperature(TEMP_C)
        hum = sensor.get_humidity()
        pres = sensor.get_atmosphere_pressure(HPA)
        light = sensor.get_luminousintensity()
        uv = sensor.get_ultraviolet_intensity(LTR390UV)

        return temp, hum, pres, light, uv

    except Exception as e:
        print("Ambient sensor error:", e)
        return None
    
def decode_ambient(data):
    try:
        temp = (data[2] << 8 | data[3]) / 100.0
        hum  = (data[4] << 8 | data[5]) / 100.0
        light = (data[6] << 8 | data[7])
        pres = (data[8] << 8 | data[9]) / 10.0
        uv = (data[10] << 8 | data[11]) / 100.0

        return temp, hum, pres, light, uv

    except Exception as e:
        print("decode error:", e)
        return None


#frame handler
def frame_handler(cam, stream, frame, log_file):
    global last_save_time
    if low_storage(1): # 1 GB threshold
        print("LOW STORAGE WARNING - stopping camera")
        
    try:
        stream.queue_frame(frame)

    except Exception as e:
        print(f"Camera stream error: {e}")

        try:
            cam.stop_streaming()
        except:
            pass

        print("Rebooting Raspberry Pi in 5 seconds...")
        time.sleep(5)

        subprocess.run(["reboot"])

        return

#     stream.queue_frame(frame)

    now = time.time()

    #save every 2 seconds
    if now - last_save_time < 2:
        return

    last_save_time = now

    #convert image
    frame.convert_pixel_format(PixelFormat.Mono10)
    img = np.squeeze(frame.as_numpy_ndarray())

    mean_val = float(np.mean(img))

    try:
        exposure = cam.ExposureTime.get()
    except Exception:
        exposure = -1

    try:
        gain = cam.Gain.get()
    except Exception:
        gain = -1

    # Auto exposure adjustment for next frame
    try:

        if mean_val < LOWER_BOUND:

            if exposure < MAX_EXPOSURE:
                print("Exp < Max Exposure")
                scale_factor = TARGET_MEAN / max(mean_val, 0.1)

                new_exposure = min(
                    exposure * scale_factor,
                    MAX_EXPOSURE
                )

                cam.ExposureTime.set(new_exposure)
                exposure = new_exposure

            elif gain < MAX_GAIN:

                new_gain = min(gain + 3.0, MAX_GAIN)

                cam.Gain.set(new_gain)
                gain = new_gain

        elif mean_val > UPPER_BOUND:

            if gain > MIN_GAIN:

                new_gain = max(gain - 3.0, MIN_GAIN)

                cam.Gain.set(new_gain)
                gain = new_gain

            else:

                scale_factor = TARGET_MEAN / mean_val

                new_exposure = max(
                    exposure * scale_factor,
                    MIN_EXPOSURE
                )

                cam.ExposureTime.set(new_exposure)
                exposure = new_exposure

    except Exception as e:
        print("Auto-exposure error:", e)

    #ambient data
    env = read_ambient()

    if env is None:
        temp = hum = pres = light = uv = -1
    else:
        temp, hum, pres, light, uv = env

    #filename
    ts = datetime.datetime.now().strftime("%m_%d_%H_%M_%S_%f")
    filename = f"frame_{ts}.fits"

    #FITS save
    hdu = fits.PrimaryHDU(img)

    hdu.header['EXPOSURE'] = exposure
    hdu.header['GAIN'] = gain
    hdu.header['MEAN'] = mean_val
    hdu.header['TEMP'] = temp
    hdu.header['HUM'] = hum
    hdu.header['PRESS'] = pres
    hdu.header['LIGHT'] = light
    hdu.header['UV'] = uv

    log_file.write(
        f"{ts},{exposure},{gain},{mean_val},"
        f"{temp},{hum},{pres},{light},{uv}\n"
    )
    log_file.flush()   # force write to disk

    hdu.writeto(filename, overwrite=True)

    print(
    f"Mean={mean_val:.2f}, "
    f"Max={img.max()}, "
    f"Exposure={exposure:.0f}, "
    f"Gain={gain:.1f}"
    )

    print("Saved:", filename)

#big function
def main():

    with VmbSystem.get_instance() as vmb:

        cams = vmb.get_all_cameras()

        print("Number of cameras found:", len(cams))

        if len(cams) == 0:
            print("No cameras found")
            return

        #print all cameras
        for i, cam in enumerate(cams):
            print()
            print("Camera index:", i)
            print("ID:", cam.get_id())
            print("Model:", cam.get_model())

        #make sure the real camera is working
        real_cam = None

        for cam in cams:
            model = cam.get_model()

            if "Simulator" not in model:
                real_cam = cam
                break

        if real_cam is None:
            print()
            print("ERROR: Only simulator cameras detected.")
            print("Your real Allied Vision camera is not being opened.")
            return

        print()
        print("Using REAL camera:")
        print("ID:", real_cam.get_id())
        print("Model:", real_cam.get_model())
        
        real_cam.set_access_mode(AccessMode.Full)
        print(f"Real cam access mode: {real_cam.get_access_mode()}")
        
        
        #log file
        log_file = open("camera_log.txt", "a")
        log_file.write(
            "timestamp,exposure,gain,mean_pixel,temp,humidity,pressure,light,uv\n"
        )

        #open camera
        with real_cam as cam:
            
            pixel_formats = cam.get_pixel_formats()
            print("Pixel formats: ")
            print(pixel_formats)
            
            

            print()
            print("Starting stream...")
            try:
                cam.ExposureAuto.set('Off')
                print("Exposure auto disabled")
            except Exception as e:
                print("ExposureAuto error:", e)

            try:
                cam.GainAuto.set('Off')
                print("Gain auto disabled")
            except Exception as e:
                print("GainAuto error:", e)
            
            # Exposure
            exp_min, exp_max = cam.ExposureTime.get_range()
            print("Exposure range:", exp_min, "to", exp_max, "us")

            # Gain
            gain_min, gain_max = cam.Gain.get_range()
            print("Gain range:", gain_min, "to", gain_max)

            print("Current exposure:", cam.ExposureTime.get())
            print("Current gain:", cam.Gain.get())
            
            print(f"Cam pixel format start: {cam.get_pixel_format()}")
            
            try:
                cam.set_pixel_format(PixelFormat.Mono10)
                print("Updated pixel format to Mono10")
            except Exception as e:
                print("Pixel format set error:", e)
            
            print(f"New cam pixel format: {cam.get_pixel_format()}")
            

            try:
                cam.start_streaming(
                    lambda c, s, f: frame_handler(cam, s, f, log_file)
                )

                while True:
                    time.sleep(1)

            except KeyboardInterrupt:
                print("Stopping...")

            except Exception as e:
                print(f"Camera failure: {e}")
                print("Rebooting in 5 seconds...")
                time.sleep(5)
                subprocess.run(["reboot"])


            except KeyboardInterrupt:
                print()
                print("Stopping...")

            cam.stop_streaming()

            print("Streaming stopped")

        log_file.close()


if __name__ == "__main__":
    main()


