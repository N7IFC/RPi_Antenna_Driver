#! /usr/bin/python3
##################################################################
#
# Raspberry Pi Antenna Driver (RPiAntDrv.py)
#
# Python GUI script to control H-Bridge via RPi.
# H-Bridge drives single DC motor tuned antenna.
#
#            Name          Call  Date(s)
# Authors:   Bill Peterson N7IFC Mar-Apr2020
#
##################################################################

from tkinter import *
from tkinter import ttk
import configparser
import RPi.GPIO as GPIO

class Window(Frame):
    # Define settings upon initialization
    def __init__(self, master=None):
        
        # parameters to send through the Frame class. 
        Frame.__init__(self, master)   

        #reference to the master widget, which is the tk window                 
        self.master = master
        
        self.encoder_count = IntVar()     # Antenna reed switch count
        self.encoder_count.set(0)
        self.motor_rev = BooleanVar()     # Reverse motor leads
        self.motor_rev.set(False)
        self.motor_running = False        # Motor running flag
        self.motor_stalled = False        # Motor stalled flag
        self.stall_active = False         # Stall detection active
        self.stall_count = 0
        self.antenna_raising = False      # Motor direction flag
        self.ant_config_sect = ("null")   # Active ini file config section
        self.ant_preset_sect = ("null")   # Active ini file preset section
        self.ant_preset_opt = ("null")    # Active ini file preset option
        self.ant_preset_val = 0           # Preset encoder target value from combobox
        
        # Run init_window, which doesn't yet exist
        self.init_window()

    #Creation of init_window
    def init_window(self):
        self.master.title('RPi Antenna Driver (v1.5)')
        # Set up root window & size (width x height + x_offset + y_offset)
        self.bg_color = 'azure'
        self.master.geometry("400x300+30+30")
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
        editmenu.add_command(label="Default ini", command=self.ini_new)
        editmenu.add_command(label="Undefined 1", command=self.about)
        editmenu.add_command(label="Undefined 2", command=self.about)
        menubar.add_cascade(label="Edit", menu=editmenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        text_1 = Label(text='Antenna', font = ('Helvetica', 14),
                       bg = self.bg_color, fg='black', padx=10, height=2, anchor=S)
        text_1.grid(row=0, column=0, columnspan=1)

        text_2 = Label(text='Motor Control', font = ('Helvetica', 14),
                       bg = self.bg_color, fg='black', padx=20, height=2, anchor=S)
        text_2.grid(row=0, column=1, columnspan=1)
        
        text_3 = Label(textvariable=self.encoder_count,
                       font = ('Helvetica', 14), bg = self.bg_color, fg='black',
                       padx=20, height=1, anchor=SW)
        text_3.grid(row=3, column=0, columnspan=1, sticky=S)
 
        text_4 = Label(text='Current Preset',
                       font = ('Helvetica', 14), bg = self.bg_color, fg='black',
                       padx=20, height=1, anchor=S)
        text_4.grid(row=3, column=1, columnspan=1, sticky=S)
        
        self.raise_button = Button(text='Raise', relief=RAISED, bd=4, padx=1,
               pady=1, height=2, width=6, font=('Helvetica', 14))
        self.raise_button.grid(row=1,column=0, padx=20, pady=5)
        self.raise_button.bind("<ButtonPress>", self.raise_button_press)
        self.raise_button.bind("<ButtonRelease>", self.RL_button_release)
        
        self.lower_button = Button(text='Lower', relief=RAISED, bd=4, padx=1,
               pady=1, height=2, width=6, font=('Helvetica', 14))
        self.lower_button.grid(row=2, column=0, padx=20, pady=5)
        self.lower_button.bind("<ButtonPress>", self.lower_button_press)
        self.lower_button.bind("<ButtonRelease>", self.RL_button_release)

        self.move_button = Button(text='Move', relief=RAISED, bd=4, padx=1,
               pady=1, height=2, width=6, font=('Helvetica', 14))
        self.move_button.grid(row=4,column=0, padx=5, pady=5)
        self.move_button.bind("<ButtonPress>", self.move_button_press)
        
        self.duty_scale = Scale(label='PWM Duty Cycle (%)', from_=1, to=100, orient = HORIZONTAL,
                               resolution = 1, length=200, command = self.update_pwm_duty)
        self.duty_scale.grid(row=1,column=1)

        self.freq_scale = Scale(label='PWM Frequency (Hz)', from_=50, to=8000, orient = HORIZONTAL,
                                resolution = 1, length=200, command = self.update_pwm_freq)
        self.freq_scale.grid(row=2,column=1)
        
        self.motor_rev_btn = Checkbutton(text="Reverse Leads", bg = self.bg_color,
                                         activebackground = self.bg_color,
                                         highlightthickness=0, variable=self.motor_rev)
        self.motor_rev_btn.grid(row=4, column=1, sticky=SW)
        
        # Antenna preset combo box is populated with values from ini file
        self.preset_combobox = ttk.Combobox(width=18, font=('Helvetica', 14),
                                            state='readonly')
        self.preset_combobox.grid(row=4, column=1, sticky=N)
        self.preset_combobox.bind("<<ComboboxSelected>>", self.get_preset_val)
        
        self.ini_test ()  # Check for ini file existence
        self.ini_read()   # Read ini file for settings       
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

    def move_button_press(self, _unused):
        self.motor_stalled = 0
        self.motor_move()
        
    def motor_up(self):
        # We can change speed on the fly
        self.pwm_set.ChangeFrequency(self.pwm_freq)
        self.pwm_set.ChangeDutyCycle(self.pwm_duty)
        # If motor is not already running and in correct direction
        if not(self.motor_running and self.antenna_raising):
            # check reverse motor lead flag
            if self.motor_rev.get() == 0:
                GPIO.output(self.dir1_pin, GPIO.HIGH) # Run motor FWD
                GPIO.output(self.dir2_pin, GPIO.LOW)
            else:
                GPIO.output(self.dir1_pin, GPIO.LOW) # Run Motor REV
                GPIO.output(self.dir2_pin, GPIO.HIGH)
            self.antenna_raising = 1
            self.motor_running = 1
            # Initialize stall counter and start stall timer
            self.motor_stall()
        
    def motor_down(self):
        # We can change speed on the fly
        self.pwm_set.ChangeFrequency(self.pwm_freq)
        self.pwm_set.ChangeDutyCycle(self.pwm_duty)
        # If motor is not running and in correct direction
        if not(self.motor_running and not self.antenna_raising):
            # check reverse motor lead flag
            if self.motor_rev.get() == 0:
                GPIO.output(self.dir1_pin, GPIO.LOW) # Run motor
                GPIO.output(self.dir2_pin, GPIO.HIGH)
            else:
                GPIO.output(self.dir1_pin, GPIO.HIGH) # Run Motor
                GPIO.output(self.dir2_pin, GPIO.LOW)
            self.motor_running = 1
            self.antenna_raising = 0
            # Initialize stall counter and start stall timer
            self.motor_stall()
        
    def motor_stop(self):
        GPIO.output(self.dir1_pin, GPIO.LOW) # Stop motor
        GPIO.output(self.dir2_pin, GPIO.LOW)
        self.pwm_set.ChangeDutyCycle(0)      # Kill PWM
        self.motor_running = 0
        #self.ini_update()

    def motor_stall(self):
        # Set stall period proportional to current motor speed
        self.stall_time = int(250)
        self.stall_period = int((100 / self.duty_scale.get())* self.stall_time)
        # If motor is still running, perform stall check
        if (self.motor_running):
            # If stall detection is not already active
            if not(self.stall_active):
                print ('stall period ' + str(self.stall_period))
                self.stall_count = self.encoder_count.get()
                self.stall_active = 1
                self.master.after(self.stall_period, self.motor_stall)
            # Otherwise see if we stalled
            elif (self.stall_count == self.encoder_count.get()):
                self.motor_stalled = 1
                self.motor_stop()
                self.stall_active = 0
                print ('We are stalled')
            # Else reset stall count and timer
            else:
                self.stall_count = self.encoder_count.get()
                print ('No stall, proceed')
                self.master.after(self.stall_period, self.motor_stall)
        else:
            self.stall_active = 0
             
    def motor_move(self):
        #print (_unused)
        # If motor is stalled, exit
        if (self.motor_stalled == 1):
            return
        # If encoder count = preset, stop and exit
        if self.encoder_count.get() == (self.ant_preset_val):
            self.motor_stop()
            print ('We have arrived')
            return
        # If encoder count within 5 counts of preset, slow down
        Lval= (self.ant_preset_val -5)
        Hval= (self.ant_preset_val +6)
        print (self.encoder_count.get())
        if self.encoder_count.get() in range(Lval, Hval):
            print ('Slow Down')
            self.duty_scale.set(25)
        # Else run full speed    
        else:
            print ('Full Speed')
            self.duty_scale.set(100)
            
        # If encoder count > preset drive antenna down
        if self.encoder_count.get() > (self.ant_preset_val):
            print ('Drive Down')
            self.motor_down()
        # Else drive antenna up
        else:
            print ('Drive Up')
            self.motor_up()
        # after 100mS, call this function again
        self.master.after(100, self.motor_move)
        
    def get_preset_val(self, _unused):
        config = configparser.ConfigParser()
        config.read ('RPiAntDrv.ini')
        #print (_unused)
        #print (self.preset_combobox.get())
        #print (config.getint(self.ant_preset_sect, self.ant_preset_opt))
        #print (config.getint(self.ant_preset_sect, self.preset_combobox.get()))        
        self.ant_preset_val = (config.getint(self.ant_preset_sect, self.preset_combobox.get()))
        print (self.ant_preset_val)
        
    def update_pwm_duty(self, _unused):
        self.pwm_duty = self.duty_scale.get()
        #print (_unused)

    def update_pwm_freq(self, _unused):
        self.pwm_freq = self.freq_scale.get()
        #print (_unused)
        
    def gpioconfig(self): # Configure GPIO pins
        GPIO.setwarnings(False)
        GPIO.cleanup()                 # In case user changes running configuration
        
        self.pwm_pin = 12      # H-Bridge PWM
        self.dir1_pin = 16     # H-Bridge control
        self.dir2_pin = 18     # H-Bridge control
        self.encoder_pin = 22  # Antenna encoder switch
        self.pwm_freq = 400    # Freq in Hz
        self.pwm_duty = 0      # Duty in percent, default to 0
        
        GPIO.setmode(GPIO.BOARD)                   # Refer to IO as Board header pins
        GPIO.setup(self.dir1_pin, GPIO.OUT)        # Direction output 1 to H-bridge
        GPIO.setup(self.dir2_pin, GPIO.OUT)        # Direction output 2 to H-bridge
        GPIO.output(self.dir1_pin, GPIO.LOW)       # Turn direction output 1 off
        GPIO.output(self.dir2_pin, GPIO.LOW)       # Turn direction output 2 off
        GPIO.setup(self.pwm_pin, GPIO.OUT)         # PWM output to H-bridge
        # Set up the simple encoder switch input and add de-bounce time in mS
        # GPIO.RISING interrupts on both edges, GPIO.FALLING seems better behaved
        GPIO.setup(self.encoder_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.encoder_pin, GPIO.FALLING, bouncetime=40, callback=self.encoder_ISR)
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
        # Set the Raspberry Pi I/O pin defaults
        config['RPiPins'] = {'pwm_pin': '12',
                             'dir1_pin': '16',
                             'dir2_pin': '18',
                             'encoder_pin': '22'}
        
        # User configurable program settings
        config['Settings'] = {'last_position':'0',
                              'ant_config_sect': 'Ant1_Config',
                              'ant_preset_sect': 'Ant1_Preset',
                              'ant_preset_opt': '20m 14.400 (037)'}
        
        # Set up default antennas
        config['Ant1_Config'] = {'name': 'Antenna1',
                               'rev_pol': 'no',
                               'pwm_freq': '4000',
                               'pwm_duty': '50',
                               'min_freq': '3500',
                               'max_freq': '29700'}
        
        config['Ant1_Preset'] = {'80m _3.500 (226)': '226',
                                  '80m _4.000 (192)': '192',
                                  '60m _5.300 (130)': '130',
                                  '60m _5.400 (127)': '127',
                                  '40m _7.000 (092)': '92',
                                  '40m _7.300 (087)': '87',
                                  '30m 10.000 (056)': '56',
                                  '30m 10.200 (054)': '54',
                                  '20m 14.000 (039)': '39',
                                  '20m 14.400 (037)': '37'}        

        config['Ant2_Config'] = {'name': 'Antenna2',
                               'rev_pol': 'yes',
                               'pwm_freq': '2000',
                               'pwm_duty': '50',
                               'min_freq': '3500',
                               'max_freq': '29700'}
        
        config['Ant2_Preset'] = {'3.500': '226',
                                  '4.000': '192',
                                  '7.000': '92',
                                  '7.300': '87',
                                  '14.000': '39',
                                  '14.400': '37'}       
        
        # Save the default configuration file
        with open('RPiAntDrv.ini', 'w') as configfile:
            config.write(configfile)
            
    def ini_test(self):
        # Test to see if configuration file exists
        try:
            with open('RPiAntDrv.ini') as _file:
                # pass condition
                print ("Ini file found")
        except IOError as _e:
            #Does not exist OR no read permissions
            print ("Unable to open Ini file, creating new one.")
            self.ini_new ()
    
    def ini_read(self):
        # Read ini file and set up parameters
        config = configparser.ConfigParser()
        config.read ('RPiAntDrv.ini')
        #print (config.get ('RPiPins', 'dir1_pin', fallback='50'))
        self.freq_scale.set(config.getint ('Ant1_Config','pwm_freq',fallback=120))
        self.duty_scale.set(config.getint ('Ant1_Config','pwm_duty',fallback=50))
        #print (config.get ('Ant1_Preset', name))
        #for section_name in config.sections():
        #    print ('Section:', section_name)
        #    print ('  Options:', config.options(section_name))
        #    for name, value in config.items(section_name):
        #        print ('  %s = %s' % (name, value))
        # Set up the active ini file section and option names
        self.ant_config_sect = (config.get ('Settings','ant_config_sect',fallback='Ant1_Config'))
        self.ant_preset_sect = (config.get ('Settings','ant_preset_sect',fallback='Ant1_Preset'))
        self.ant_preset_opt = (config.get ('Settings','ant_preset_opt',fallback='none'))
        # Set up and populate the antenna preset combobox
        self.preset_combobox['values']=(config.options(self.ant_preset_sect))
        self.preset_combobox.set(self.ant_preset_opt)
        # Set the encoder count to preset value
        print (config.getint(self.ant_preset_sect, self.ant_preset_opt))
        #self.encoder_count.set (config.getint(self.ant_preset_sect, self.ant_preset_opt))
        self.encoder_count.set (config.getint('Settings','last_position',fallback=0))
        
    def ini_update(self):
        config = configparser.ConfigParser()
        print ('updating ini')
        # Perform read-modify-write of ini file
        # Note: Anytyhing written must be a string value
        config.read ('RPiAntDrv.ini')
        config.set('Settings','last_position',str(self.encoder_count.get()))

        # Save modified configuration file
        with open('RPiAntDrv.ini', 'w') as configfile:
            config.write(configfile)
            
    def close(self): # Cleanly close the GUI and cleanup the GPIO
        self.ini_update()   # Save current settings
        GPIO.cleanup()
        self.master.destroy()
        print ("GPIO cleanup executed")
        
    def about(self):
        popup = Toplevel()
        popup.title("About RPiAntDrv")
        popup.geometry("350x250+30+30")
        popup.configure(bg= 'snow')
        
        popup_text1 = Label(popup, text='RPiAntDrv.py   v1.5',
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
