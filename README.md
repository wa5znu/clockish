# Clockish - WA5ZNU github/waznu

This MicroPython script is for the rp2040-lcd-1.28 and SymRFT60 or
similar WWVB receiver. The script will draw a circle around the center
of the display, with each 6-degree segment colored white. The segments
that are 1 or 2 in the samples array will be drawn closer to the
center, while the segments that are 0 will be drawn at the
edge. Invalid samples are drawn at 4, closest to the center.

# Features
- Uses the rp2040-lcd-1.28 display and SymRFT60 WWVB receiver
- Draws a circle with segments colored based on WWVB samples
- Handles invalid samples by drawing them closer to the center

# Installation
- Clone the repository: git clone https://github.com/waznu/Clockish.git
- Connect the rp2040-lcd-1.28 display and SymRFT60 WWVB receiver to your microcontroller
- Update the pin numbers in the script to match your hardware setup
- Upload the script to your microcontroller using a tool like Thonny or Mu Editor

# Usage
- Connect the rp2040-lcd-1.28 display and SymRFT60 WWVB receiver to your microcontroller
- Update the pin numbers in the script to match your hardware setup
- Upload the script to your microcontroller using a tool like Thonny or Mu Editor
- Run the script on your microcontroller

# License
This project is licensed under the MIT License - see the LICENSE file for details.
