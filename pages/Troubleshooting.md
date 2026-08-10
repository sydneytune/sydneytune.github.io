This page will detail how to troubleshoot common problems with spectrometers.  
  
###Focusing:  
The most common issue with building a spectrometer is getting it correctly focused. It can be very difficult and sometimes frustrating since there are multiple parts to move and orient correctly. Here are some tips for focusing your instrument  
- Use a live viewer like ASI Studio or VimbaX Viewer to see the picture in live time. You can set these to loop every 1 second or so to see the changes you are making.  
- The first step is always to focus the camera component. Use just the camera and focusing lens for this part. Move the lens forward and backwards until the picture is clear. You want to focus the camera "at infinity". This means focusing on something far in the distance like a tree line or tall building.  
- Once the camera is focused, you can start adding the next lenses, grating, and slit in steps to align it as you go. For freeform spectrometers, you can hold a small piece of paper, like a notecard, in between each component to track the light as it moves towards the detector. Moving the grating can change which part of the spectra you are looking at. For example, rotating the Sol'Ex grating changes which wavelengths you are looking at.  
- The slit is usually aligned vertically (perpendicular with respect to the horizon) to see the most of the spectrum at once. This will show vertical absorption/emission features across the image.  
- Once you get your instrument focused, make sure that you have a way to keep it like that so you don't have to re-align it the next time you use it. This can be by marking the spot, taping it into place, or designing your casing to fit snugly. It can be very time consuming to focus it multiple times.  

###Light Leakage:  
Another common problem is extraneous light leaking into the spectrometer and onto the sensor. This will mess up the collected data. Here are some common causes and fixes  
- Light leaking through the exterior casing after being screwed together is very common. To fix this, you can add lips to the edges of your casing print. You can also tape the seams of the casing once you have all of the components inside aligned.  
- Sometimes the image can get blown out but you can't pinpoint the exact location of the leak. This could be because of your casing material. While test prints can be made in any color to check sizing, final prints should be printed with black filament (or another dark color) to block all light.  
- For the Sol'Ex spectrometer, we had light leaking in near the diffraction grating wheel at one point. Once we got the grating rotated to our preferred wavelengths, we had to cover up the rest of the screw holes.