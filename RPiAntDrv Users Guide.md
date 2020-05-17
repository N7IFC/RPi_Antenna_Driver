# Users Guide for the Raspberry Pi Antenna Driver

### INTRODUCTION:

RPiAntDrv.py is a Python GUI program script written for the Raspberry Pi (RPi) for antenna control. The script controls a DC motor-tuned antenna via an H-Bridge and pulse encoder feedback. The H-Bridge drives a single DC motor using Pulse Width Modulation (PWM). The antenna must contain a simple pulse encoder output such as a reed switch activated by the antenna's drive mechanism. One compatible antenna is called a "Screwdriver Antenna" such as those made by Scorpion Antennas, Tarheel Antennas, Hi-Q-Antennas™, among others. Another antenna might be a tuned loop with a multi-turn variable capacitor.
 
Due to the fast response of the Raspberry Pi hardware I/O, it is highly recommended the encoder signal be conditioned and isolated with an opto-coupler and Schmitt trigger. One such integrated circuit that contains both is the ON Semiconductor / Fairchild H11L1M. An example circuit will be available in this repository soon.

The application program supports multiple antenna profiles so that the same hardware may be used to control different antennas or different configurations of the same antenna. for example, a single screwdriver antenna may have several whip lengths, a capacity hat or a top wire added to get on 160 meters. Each of these configurations may be considered a different antenna by the program and easily selected by the user.

### DISCLAIMER:

The author(s) are not responsible for the use or misuse of this application program or example hardware. Safe use of the program and hardware is the sole responsibility of the end user. Refer to the MIT license.

### 1.0 INSTALLATION:

**1.1.** If you are updating to a new version of RPiAntDrv.py, make a back-up copy of the RPiAntDrv.ini file for reference as it may be incompatible with the new version. Delete or rename the old RPiAntDrv.ini file in the `/home/pi/bin/` directory.

**1.2.** Copy the Python script "RPiAntDrv.py" to the Raspberry Pi `/home/pi/bin/` directory.

**1.3.** Change permissions for RPiAntDrv.py to make it executable using command line or file manager.

**1.4.** Open a terminal window and run the script using terminal command RPiAntDrv.py

**1.5.** Upon first running the script, a file called RPiAntDrv.ini will be created. This ini file must be edited to set up your particular antenna.

**1.6.** A RPiAntDrv.desktop file can be created in the directory `/usr/share/applications/` and added to the Raspberry Pi desktop menu structure if you desire. An example desktop file and icon are available in the repository (RPiAntDrv.desktop, RPiAntDrv_icon.png). Place the icon file under `usr/share/icons` or `usr/share/pixmaps`.

### 2.0 INITIAL SETUP:

**2.1.** If not done previously, run the Python script "RPiAntDrv.py" in the `/home/pi/bin/` directory. This will create a default configuration file called RPiAntDrv.ini in the `/home/pi/bin/` directory. Once this file is created close the RPi Antenna Driver application.

**2.2.** Open the RPiAntDrv.ini in the `/home/pi/bin/` directory using a text editor such as Mousepad or nano.

**2.3.** The first section of the ini file should look similar to the following:

	[Settings]  
	pwm_pin = 13  
	dir1_pin = 15  
	dir2_pin = 19  
	encoder_pin = 11  
	antennas = Antenna 1, Antenna 2  
	last_position = 38  
	last_antenna = Antenna 1  
	last_preset = 20m 14.200 (038)  

**2.4.** Set the RPi output header pins to match your hardware configuration. It is highly suggested to use pins that are logic low (0V) when the RPi is first booted. On the RPi model 4b header, suitable pins are typically 8, 11, 13, 15, 16, 18, 19, 21, 22, 23, 32, 33, 35, 36, 37, 38, and 40. Only connect these pins to 3V logic level circuits.

**2.5.** The pwm_pin output will have the pulse width modulation signal on it when the antenna is called to move. The duty cycle of this output varies with commanded speed. The frequency of the PWM signal is set in each antenna configuration section using the key value called pwm_freq.

**2.6.** The direction output pins (dir1_pin, dir2_pin) are used to control the H-bridge and motor direction. Some H-bridges may only require a single pin to change motor direction and the dir1_pin is typically used. If you find that the motor drives the wrong direction, swap the motor leads at the output of the H-bridge.

**2.7.** The encoder_pin input is used to detect if the motor is running and also used to keep track of antenna tuning position. See circuit recommendations in the INTRODUCTION section above.

**2.8.** The [Settings] 'antennas' key forms the list of antennas that the user may select from. Each antenna in the comma-separated list must have two corresponding sections in the ini file that contain the specifics for a given antenna. The name of the antenna used must exactly match the corresponding section names with "_Config" and "_Preset" appended to the end of the antenna name. For example, if we wanted to rename "Antenna 1" to "Freds Antenna" then the [Settings] 'antennas' key values would be changed to read:

	antennas = Freds Antenna, Antenna 2

Additionally we would need to rename the following two sections ([Antenna 1_Config] and [Antenna 1_Preset]) to ([Freds Antenna_Config] and [Freds Antenna_Preset]). This way the program will know where to find the settings for Freds Antenna.

The default ini file defines two antennas but more may be added if desired by adding the antenna name in the [Settings] section and the corresponding  "AntennaName_Config" and "AntennaName_Preset" sections.

**2.9.** The [Settings] keys 'last_position', 'last_antenna', and 'last_preset' are used by the program to save the last used configuration when the application is exited. There is no need to edit these keys as they will be updated on program exit.

**2.10.** Each antenna has a configuration section that looks similar to the following:

	[Antenna 1_Config]  
	pwm_freq = 4000  
	full_speed = 100  
	slow_speed = 25  
	stall_time = 250  

**2.11.** The key 'pwm_freq' is used to set the motor pwm frequency in Hz. Typically this is set to about 4,000 Hz for DC brushed motors in order to have good low speed torque and fairly quiet operation. The optimum value for your motor may be found experimentally and set in the ini file. It is suggested to stay below 20,000 as the pwm is software generated and switching losses also increase with frequency.

**2.12.** The key 'full_speed' is used to set the % speed the motor will run when driving to a preset. The range is 1 to 100 percent (default 100).

**2.13.** The key 'slow_speed' is used to set the % speed the motor will run when approaching a preset. This is useful to prevent overshooting a target preset value. The range is 1 to 100 percent (default 25).

**2.14.** The key 'stall_time' is the time in milliseconds where the program expects to see a pulse from the motor encoder when running at 100% speed. The program will automatically extend this time when running below 100% speed. If the program does not see an encoder pulse within the stall time, it will turn off power to the motor and notify the user of a stall event. If the antenna may be damaged by a stall condition (such as a hard stop), it is suggested that other hardware protections are installed such as a PTC auto-resetting fuse sized below the motors locked rotor current... The stall_time value may be found experimentally by starting around 100mS (0.1 seconds) and increasing the value until the antenna does not trigger a stall event under normal operation. The range is 10 to ~ 5,000 milliseconds (0.01 to 5 seconds, default 250mS).

### 3.0 ANTENNA PRESETS:

**3.1.** Antenna presets may be added or edited any time by opening the RPiAntDrv.ini in the `/home/pi/bin/` directory using a text editor such as Mousepad or nano.

**3.2.** Presets are stored as key = value pairs where the key is available to the user to select from and the value is the antenna's encoder value for that preset. The key names are always lower case and may be up to 20 characters long. An example preset section list may look like the following:

	[Antenna 2_Preset] 
	maximum    (270) = 270  
	80m _3.700 (200) = 200  
	60m _5.350 (129) = 129  
	40m _7.250 (090) = 90  
	30m 10.100 (055) = 55  
	20m 14.200 (038) = 38  
	minimum    (000) = 0  

**3.3.** As mentioned in section 2 above, the preset section name must match the antenna name with "_Preset" appended to the antenna name.

**3.4.** If the presets for your antenna configuration are unknown, they may be found experimentally. For a screwdriver antenna we might start with the antenna fully retracted (highest frequency) and call this our zero point or minimum encoder count position. Run the RPi Antenna Driver application and press the Lower button to drive the antenna to its lowest position (motor may stall). The encoder count will be shown in the upper left of the window. This number may be zeroed by selecting a default "Preset Selection" of "minimum (000)", then click Edit and Sync Count and confirm the action. Your antenna should now be at its lowest position and the encoder value should be "0".

**3.5.** Using the Raise and Lower buttons, tune the antenna manually to the desired frequency. Note the frequency preset and encoder count value. Repeat this process until you have the desired number of preset and encoder count values recorded.

**3.6.** Edit the RPiAntDrv.ini file with the recorded preset key = value pairs. These presets will now be available to use the next time the application is run.

**3.7.** Back-up the RPiAntDrv.ini file in a safe place so that presets may be restored if the Raspberry Pi file system becomes unusable.

### 4.0 GRAPHICAL USER INTERFACE

![Alt text](RPiAntDrv_Screenshot.png?raw=true "Screenshot")

**4.1.** The GUI has a familiar windowed layout with some menu features not implemented. For operations not supported, the "About" window will be displayed.

**4.2.** Encoder Count - This value is displayed in the upper left of the window and shows the antennas current position.

**4.3.** Status Bar - Displays status messages (such as motor stall events) as the program runs.

**4.4.** Raise and Lower Buttons - Used to manually control the antenna.

**4.5.** Preset Button - Once a Preset Selection has been made, pressing this button will automatically drive the antenna to the preset position. The antenna will drive at full speed until nearing the preset where it will then slow and attain the preset.

**4.6.** Motor Speed - This sliding control is used to vary antenna tuning speed 1 - 100% speed.

**4.7.** Antenna Selection - Is used to select the desired antenna configuration. Changing the antenna selection loads the configuration and presets for the newly selected antenna.

**4.8.** Preset Selection - Allows user to select user-defined presets.

**4.9.** Edit > Default ini - This operation will overwrite the RPiAntDrv.ini file in case it gets unusable for some reason or if the user wants to start fresh again.

**4.10.** Edit > Sync Count - This operation will synchronize the encoder count value with the selected preset. In cases where the encoder value drifts slightly during operation, the user may manually tune the antenna to a known preset and then synchronize to this preset to resume normal operation.

**4.11.** Help > About - Displays the about pop-up window.

-End-
