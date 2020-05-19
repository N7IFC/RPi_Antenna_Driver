#! /usr/bin/python3
##################################################################
#
# Raspberry Pi Antenna Driver (RPiAntDrv.py)
#
# Python GUI script to control H-Bridge via RPi.
# H-Bridge drives single DC motor tuned antenna.
#
#            Name          Call  Date(s)
# Authors:   Bill Peterson N7IFC Mar-May2020
#
##################################################################

from tkinter import Tk, ttk, messagebox, Frame, Menu, Label, Button
from tkinter import Scale, IntVar, StringVar, Toplevel
from tkinter import RAISED, HORIZONTAL, LEFT, S, W, SW, NW
from pathlib import Path
import configparser
import RPi.GPIO as GPIO

class Window(Frame):
    # Define settings upon initialization
    def __init__(self, master=None):
        
        # parameters to send through the Frame class. 
        Frame.__init__(self, master)   
        
        #reference to the master widget, which is the tk window                 
        self.master = master
        
        # Retrieve parent script directory for absolute addressing
        self.base_path = Path(__file__).parent
        self.ini_path = str(self.base_path)+'/RPiAntDrv.ini'
        #print (self.ini_path)
        
        # Raspberry Pi I/O pins get reassigned when ini file is read
        self.pwm_freq = 4000   # PWM Freq in Hz
        self.pwm_duty = 0      # PWM Duty in percent, default to 0%
        self.stall_time = 250  # Motor stall time in mS
        
        self.encoder_count = IntVar()     # Antenna reed switch count
        self.encoder_count.set(0)
        self.motor_running = False        # Motor running flag
        self.motor_stalled = False        # Motor stalled flag
        self.stall_active = False         # Stall detection active
        self.stall_count = 0              # Encoder count during stall detection
        self.full_speed = 100             # Full speed PWM duty cycle
        self.slow_speed = 25              # Slow speed PWM duty cycle
        self.antenna_raising = False      # Motor direction flag
        self.ant_config_sect = ("null")   # Active ini file config section
        self.ant_preset_sect = ("null")   # Active ini file preset section
        self.ant_preset_val = 0           # Preset encoder target value from ini presets
        self.status_message = StringVar() # Status message text for text_2
        
        # Run init_window, which doesn't yet exist
        self.init_window()
        
    #Creation of init_window
    def init_window(self):
        self.master.title('RPi Antenna Driver (v1.6)')
        # Set up root window & size (width x height + x_offset + y_offset)
        self.bg_color = 'azure'
        self.master.geometry("350x275+150+100")
        self.master.configure(bg= self.bg_color)
        
        # Create menu entry and sub-options
        menubar = Menu(self.master)
        self.master.config(menu=menubar)        
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open", command=self.about)
        filemenu.add_command(label="Save", command=self.about)
        filemenu.add_command(label="Save as...", command=self.about)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self.close)
        menubar.add_cascade(label="File", menu=filemenu)
        
        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Default ini", command=self.confirm_newini)
        editmenu.add_command(label="Sync Count", command=self.confirm_sync)
        editmenu.add_command(label="Undefined 2", command=self.about)
        menubar.add_cascade(label="Edit", menu=editmenu)
        
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.about)
        menubar.add_cascade(label="Help", menu=helpmenu)
        
        text_1 = Label(textvariable=self.encoder_count, font = ('Helvetica', 30),
                       bg = self.bg_color, fg='black', pady=5, height=1)
        text_1.grid(row=0, column=0, rowspan=2, pady=1, sticky=S)
        
        text_2 = Label(text='Status:', font = ('Helvetica', 14),
                       bg = self.bg_color, fg='black', height=1,
                       anchor=SW, width=22, justify=LEFT)
        text_2.grid(row=0, column=1, columnspan=1, sticky=SW)
        
        text_3 = Label(textvariable=self.status_message, font = ('Helvetica', 12),
                       bg='white', fg='black', height=1, anchor=NW, width=22,
                       borderwidth=1, relief="solid")
        text_3.grid(row=1, column=1, sticky=NW)
        
        text_4 = Label(text='Motor Speed (%):', font = ('Helvetica', 14),
                       bg = self.bg_color, fg='black', padx=1, height=1,
                       anchor=SW, width=22, justify=LEFT)
        text_4.grid(row=2, column=1, columnspan=1, sticky=S)
        
        text_5 = Label(text='Antenna Selection:', font = ('Helvetica', 14),
                       bg = self.bg_color, fg='black', padx=1, height=1,
                       anchor=SW, width=22, justify=LEFT)
        text_5.grid(row=4, column=1, columnspan=1, sticky=S)
        
        text_6 = Label(text='Preset Selection:',  font = ('Helvetica', 14),
                       bg = self.bg_color, fg='black', padx=1, height=1,
                       anchor=W, width=22, justify=LEFT)
        text_6.grid(row=6, column=1, columnspan=1, sticky=S)
        
        self.raise_button = Button(text='Raise', relief=RAISED, bd=4, padx=1,
               pady=1, height=2, width=6, font=('Helvetica', 14))
        self.raise_button.grid(row=2, column=0, padx=20, pady=5, rowspan=2)
        self.raise_button.bind("<ButtonPress>", self.raise_button_press)
        self.raise_button.bind("<ButtonRelease>", self.RL_button_release)
        
        self.lower_button = Button(text='Lower', relief=RAISED, bd=4, padx=1,
               pady=1, height=2, width=6, font=('Helvetica', 14))
        self.lower_button.grid(row=4, column=0, padx=20, pady=5, rowspan=2)
        self.lower_button.bind("<ButtonPress>", self.lower_button_press)
        self.lower_button.bind("<ButtonRelease>", self.RL_button_release)
        
        self.preset_button = Button(text='Preset', relief=RAISED, bd=4, padx=1,
               pady=1, height=2, width=6, font=('Helvetica', 14))
        self.preset_button.grid(row=6, column=0, padx=5, pady=5, rowspan=2)
        self.preset_button.bind("<ButtonPress>", self.preset_button_press)
        
        self.duty_scale = Scale(from_=1, to=100, orient = HORIZONTAL,
                                resolution = 1, length=200,
                                command = self.update_pwm_duty)
        self.duty_scale.grid(row=3,column=1, sticky=NW)
        
        # Antenna preset combo box is populated with values from ini file
        self.antenna_combobox = ttk.Combobox(width=19, font=('Helvetica', 14),
                                            state='readonly')
        self.antenna_combobox.grid(row=5, column=1, sticky=NW)
        self.antenna_combobox.bind("<<ComboboxSelected>>", self.get_antenna_val)
        
        # Antenna preset combo box is populated with values from ini file
        self.preset_combobox = ttk.Combobox(width=19, font=('Helvetica', 14),
                                            state='readonly')
        self.preset_combobox.grid(row=7, column=1, sticky=NW)
        self.preset_combobox.bind("<<ComboboxSelected>>", self.get_preset_val)
        
        self.ini_test ()  # Check for ini file existence
        self.ini_read()   # Retrieve ini file settings       
        self.gpioconfig() # Set up GPIO for antenna control
        
        return
        
    def raise_button_press(self, _unused):
        self.motor_stalled = 0
        self.motor_up ()
        
    def lower_button_press(self, _unused):
        self.motor_stalled = 0
        self.motor_down ()
        
    def RL_button_release(self, _unused):
        self.motor_stop ()
        self.status_message.set ("Ready")
        
    def preset_button_press(self, _unused):
        self.motor_stalled = 0
        self.motor_move()
        
    def confirm_newini(self):
        okay = messagebox.askokcancel('RPiAntDrv',
                                        'Overwrite Configuration File?',
                                        detail='This will overwrite the '
                                      'RPiAntDrv.ini file with default '
                                      'values.', icon='question')
        if okay:
            # Overwrite the ini file and refresh values
            self.ini_new()
            self.ini_read()
            self.status_message.set ("RPiAntDrv.ini written")
        else:
            self.status_message.set ("Operation cancelled")
            
    def confirm_sync(self):
        okay = messagebox.askokcancel('RPiAntDrv',
                                        'Proceed with Sync?',
                                        detail='This will sychronize the '
                                      'antenna encoder count to the preset '
                                      'value selected.', icon='question')
        if okay:
            # Sychronize encoder count with current preset value
            self.encoder_count.set(self.ant_preset_val)
            self.status_message.set ("Encoder syncronized")
        else:
            self.status_message.set ("Encoder sync canceled")
        
    def motor_up(self):
        # We can change speed on the fly
        self.pwm_set.ChangeDutyCycle(self.pwm_duty)
        # If motor is not already running and in correct direction
        if not(self.motor_running and self.antenna_raising):
            # check reverse motor lead flag
            GPIO.output(self.dir1_pin, GPIO.HIGH) # Run motor FWD
            GPIO.output(self.dir2_pin, GPIO.LOW)
            self.antenna_raising = 1
            self.motor_running = 1
            # Initialize stall counter and start stall timer
            self.motor_stall()
        
    def motor_down(self):
        # We can change speed on the fly
        self.pwm_set.ChangeDutyCycle(self.pwm_duty)
        # If motor is not running and in correct direction
        if not(self.motor_running and not self.antenna_raising):
            GPIO.output(self.dir1_pin, GPIO.LOW) # Run motor
            GPIO.output(self.dir2_pin, GPIO.HIGH)
            self.motor_running = 1
            self.antenna_raising = 0
            # Initialize stall detection
            self.motor_stall()
        
    def motor_stop(self):
        GPIO.output(self.dir1_pin, GPIO.LOW) # Stop motor
        GPIO.output(self.dir2_pin, GPIO.LOW)
        self.pwm_set.ChangeDutyCycle(0)      # Kill PWM
        self.motor_running = 0
        #self.ini_update()

    def motor_stall(self):
        # Set stall period proportional to motor speed
        self.stall_period = int((100 / self.duty_scale.get())* self.stall_time)
        # If motor is still running, perform stall check
        if (self.motor_running):
            # If stall detection is not already active
            if not(self.stall_active):
                self.stall_count = self.encoder_count.get()
                self.stall_active = 1
                self.master.after(self.stall_period, self.motor_stall)
            # Otherwise see if we stalled
            elif (self.stall_count == self.encoder_count.get()):
                self.motor_stalled = 1
                self.motor_stop()
                self.stall_active = 0
                self.status_message.set ("! Antenna Stalled !")
            # Else reset stall count and timer
            else:
                self.stall_count = self.encoder_count.get()
                self.master.after(self.stall_period, self.motor_stall)
        else:
            self.stall_active = 0
            
    def motor_move(self):
        # If motor is stalled, exit
        if (self.motor_stalled == 1):
            return
        # If encoder count = preset, stop and exit
        if self.encoder_count.get() == (self.ant_preset_val):
            self.motor_stop()
            self.status_message.set ("We have arrived")
            return
        # If encoder count within 5 counts of preset, slow down
        Lval= (self.ant_preset_val -5)
        Hval= (self.ant_preset_val +6)
        if self.encoder_count.get() in range(Lval, Hval):
            self.status_message.set ("Slowing down")
            self.duty_scale.set(self.slow_speed)
        # Else run full speed    
        else:
            self.status_message.set ("Full speed")
            self.duty_scale.set(self.full_speed)
            
        # If encoder count > preset drive antenna down
        if self.encoder_count.get() > (self.ant_preset_val):
            self.motor_down()
        # Else drive antenna up
        else:
            self.motor_up()
        # after 100mS, call this function again
        self.master.after(100, self.motor_move)
        
    def get_antenna_val(self, _unused):
        # fetch new antenna configuration and presets
        config = configparser.ConfigParser()
        config.read (self.ini_path)
        self.last_antenna = self.antenna_combobox.get()
        self.ant_refresh(config)
        self.pwm_set.ChangeFrequency(self.pwm_freq)
        
    def get_preset_val(self, _unused):
        # get the preset value stored in the ini file
        config = configparser.ConfigParser()
        config.read (self.ini_path)
        self.ant_preset_val = (config.getint(self.ant_preset_sect,
                                             self.preset_combobox.get()))
        #print (self.ant_preset_val)
        
    def update_pwm_duty(self, _unused):
        self.pwm_duty = self.duty_scale.get()
        #print (_unused)
        
    def gpioconfig(self): # Configure GPIO pins
        GPIO.setwarnings(False)
        GPIO.cleanup()                 # In case user changes running configuration
        
        GPIO.setmode(GPIO.BOARD)                   # Refer to IO as Board header pins
        GPIO.setup(self.dir1_pin, GPIO.OUT)        # Direction output 1 to H-bridge
        GPIO.setup(self.dir2_pin, GPIO.OUT)        # Direction output 2 to H-bridge
        GPIO.output(self.dir1_pin, GPIO.LOW)       # Turn direction output 1 off
        GPIO.output(self.dir2_pin, GPIO.LOW)       # Turn direction output 2 off
        GPIO.setup(self.pwm_pin, GPIO.OUT)         # PWM output to H-bridge
        # Set up the simple encoder switch input and add de-bounce time in mS
        # GPIO.RISING interrupts on both edges, GPIO.FALLING seems better behaved
        GPIO.setup(self.encoder_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.encoder_pin, GPIO.FALLING,
                              bouncetime=40, callback=self.encoder_ISR)
        # Note GPIO.PWM is software not hardware PWM
        self.pwm_set = GPIO.PWM(self.pwm_pin, self.pwm_freq) # Set up PWM for use
        #self.pwm_set.stop()                       # Stop pwm output
        self.pwm_set.start(self.pwm_duty)          # Start pwm output at 0%
        
        GPIO.setwarnings(True)
        
    def encoder_ISR(self, _channel):
        # Do as little as possible in the ISR, get in and get out!
        # Increment the encoder count and jump out
        if self.antenna_raising == 1:
            self.encoder_count.set (self.encoder_count.get()+1)
        else:
            self.encoder_count.set (self.encoder_count.get()-1)
            
    def ini_new(self): # Set up an ini file if it does not exist
        # Configuration file parser to read and write ini file
        config = configparser.ConfigParser()
        # User configurable program settings
        config['Settings'] = {'pwm_pin':'19',
                              'dir1_pin':'13',
                              'dir2_pin':'15',
                              'encoder_pin':'11',
                              'antennas':'Antenna 1, Antenna 2',                              
                              'last_position':'0',
                              'last_antenna':'Antenna 1',
                              'last_preset':'20m 14.400 (037)'}
        
        # Set up default antennas
        config['Antenna 1_Config'] = {'pwm_freq':'4000',
                                      'full_speed':'100',
                                      'slow_speed':'25',
                                      'stall_time':'250'}
        
        config['Antenna 1_Preset'] = {'maximum    (270)':'270',
                                      '80m _3.500 (226)':'226',
                                      '80m _3.580 (221)':'221',
                                      '80m _3.800 (206)':'206',
                                      '80m _3.900 (199)':'199',
                                      '80m _4.000 (192)':'192',
                                      '60m _5.300 (130)':'130',
                                      '60m _5.400 (127)':'127',
                                      '40m _7.035 (091)':'91',
                                      '40m _7.175 (089)':'89',
                                      '40m _7.300 (087)':'87',
                                      '30m 10.000 (056)':'56',
                                      '30m 10.100 (055)':'55',
                                      '30m 10.200 (054)':'54',
                                      '20m 14.000 (039)':'39',
                                      '20m 14.200 (038)':'38',
                                      '20m 14.400 (037)':'37',
                                      '15m 21.275 (019)':'19',
                                      '12m 24.930 (014)':'14',
                                      '10m 28.000 (008)':'8',
                                      '10m 29.700 (006)':'6',
                                      'minimum    (000)':'0'}        
        
        config['Antenna 2_Config'] = {'pwm_freq':'4000',
                                      'full_speed':'95',
                                      'slow_speed':'20',
                                      'stall_time':'250'}
        
        config['Antenna 2_Preset'] = {'maximum    (270)':'270',
                                      '80m _3.700 (200)':'200',
                                      '60m _5.350 (129)':'129',
                                      '40m _7.250 (090)':'90',
                                      '30m 10.100 (055)':'55',
                                      '20m 14.200 (038)':'38',
                                      'minimum    (000)':'0'}
        
        # Save the default configuration file
        with open(self.ini_path, 'w') as configfile:
            config.write(configfile)
            
    def ini_test(self):
        # Test to see if configuration file exists
        try:
            with open(self.ini_path) as _file:
                # pass condition
                self.status_message.set ("Configuration file loaded")
        except IOError as _e:
            #Does not exist OR no read permissions
            self.status_message.set ("Configuration file created")
            self.ini_new ()
            
    def ini_read(self):
        # Read ini file and set up parameters
        config = configparser.ConfigParser()
        config.read (self.ini_path)
        # Retrieve I/O pin assignments
        self.pwm_pin = (config.getint ('Settings','pwm_pin',fallback=19))
        self.dir1_pin = (config.getint ('Settings','dir1_pin',fallback=13))
        self.dir2_pin = (config.getint ('Settings','dir2_pin',fallback=15))
        self.encoder_pin = (config.getint ('Settings','encoder_pin',fallback=11))
        # Restore the encoder count to preset value
        self.encoder_count.set (config.getint('Settings','last_position',fallback=0))
        self.ant_preset_val = self.encoder_count.get()       
        # Retrieve the last antenna used and restore saved state
        # Grab CSV list of antennas to act as combobox values and keys
        # The .strip method removes leading and trailing spaces from .split list
        _antennas = (config.get('Settings','antennas',fallback="Antenna 1"))
        self.antenna_combobox['values']=[item.strip() for item in _antennas.split(',')]         
        self.last_antenna = (config.get('Settings','last_antenna',fallback="Antenna 1"))
        self.antenna_combobox.set(self.last_antenna)
        self.preset_combobox.set(config.get('Settings','last_preset',fallback='None'))
        
        # refresh antenna settings and presets
        self.ant_refresh(config)
        
    def ant_refresh (self,config):
        # Using selected antenna refresh antenna settings and presets
        self.ant_config_sect = (self.last_antenna + '_Config')
        self.ant_preset_sect = (self.last_antenna + '_Preset')
        self.pwm_freq = (config.getint (self.ant_config_sect,'pwm_freq',fallback=4000))
        self.full_speed = (config.getint (self.ant_config_sect,'full_speed',fallback=100))
        self.slow_speed = (config.getint (self.ant_config_sect,'slow_speed',fallback=25))
        self.stall_time = (config.getint (self.ant_config_sect,'stall_time',fallback=250))
        self.preset_combobox['values']=(config.options(self.ant_preset_sect))
        
    def ini_update(self):
        config = configparser.ConfigParser()
        # Perform read-modify-write of ini file
        # Note: Anytyhing written must be a string value
        config.read (self.ini_path)
        config.set ('Settings','last_position',str(self.encoder_count.get()))
        config.set ('Settings','last_antenna',self.antenna_combobox.get())
        config.set ('Settings','last_preset',self.preset_combobox.get())     
        # Save modified configuration file
        with open(self.ini_path, 'w') as configfile:
            config.write(configfile)
        self.status_message.set ("ini file updated")
        
    def close(self): # Cleanly close the GUI and cleanup the GPIO
        self.ini_update()   # Save current settings
        GPIO.cleanup()
        #print ("GPIO cleanup executed")        
        self.master.destroy()
        #print ("master window destroyed")
        
    def about(self):
        popup = Toplevel()
        popup.title("About RPiAntDrv")
        popup.geometry("325x225+162+168")
        popup.configure(bg= 'snow')
        
        popup_text1 = Label(popup, text='RPiAntDrv.py   v1.6',
                           font = ('Helvetica', 12), wraplength=300, justify=LEFT,
                           bg = 'snow', fg='black', padx=10, pady=10)
        popup_text1.grid(row=0, column=0, columnspan=1)
        
        popup_text2 = Label(popup, text='This Python script is used to control '
                            'a motor tuned antenna like a screwdriver antenna or '
                            'tuned loop. Feedback from the antenna is provided by '
                            'a simple dry contact or pulse output relative to the '
                            'output shaft turning.',
                           font = ('Helvetica', 12), wraplength=300, justify=LEFT,
                           bg = 'snow', fg='black', padx=10, pady=10)
        popup_text2.grid(row=1, column=0, columnspan=1)
        
        popup.mainloop()
        
def main():
    
    # root window created. Here, that would be the only window, but
    # you can later have windows within windows.
    root = Tk()
    app = Window(root) #creation of an instance
    root.protocol("WM_DELETE_WINDOW", app.close) # cleanup GPIO when X closes window
    root.mainloop() # Loops forever
    
if __name__ == '__main__':
    main()
    