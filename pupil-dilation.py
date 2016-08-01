# This is a pupil light reflex script

# by Jan Freyberg (jan.freyberg@kcl.ac.uk)

# This script displays short flashes of white light and measures the pupil
# dilation using a tobii eye tracker


from psychopy import visual, core, parallel, event, monitors, gui
import random
import numpy as np
import os
import os.path
from tobiicontroller import TobiiController as tobiicontroller
from datetime import datetime

# Stimulus and Experiment Parameters
preflash = 1.6  # time in seconds before the flash
prejitter = 0.8  # time by which the onset can randomly vary
flashduration = 0.120  # flash duration in seconds
postflash = 3.0  # time in seconds after the flash
breaktime = 3.0
darklevel = -1.0  # the color value for dark periods
flashlevel = 1.0  # the color value for flashes
n = 20  # the number of trials
tobiiid = 'TX300-010103441611'  # the tracker id (get from eyetrackerbrowser)

triggvalues = {'flash start': 10,
               'flash end': 99}

# get info from gui
sessionInfo = {'subject': 'test',
               'time': datetime.now().strftime('%Y-%m-%d %H-%M')}
dialog = gui.DlgFromDict(dictionary=sessionInfo,
                         title='Pupil Dilation')
# check the dialog box was OK
assert dialog.OK, "You cancelled the experiment during the dialog box."

# Make a folder to store the data
datadir = os.path.join(os.getcwd(), 'data',
                       sessionInfo['time'] + ' ' + sessionInfo['subject'],
                       '')
os.makedirs(datadir)


# Screen Parameters
screenrate = 60.0  # screen rate in Hz
debugging = False  # set True if you want a smaller window to still see code

# Set the screen parameters: (This is important!)
screen = monitors.Monitor('tobiix300')
screen.setSizePix([1920, 1080])
screen.setWidth(51)  # screen width in cm
screen.setDistance(60)  # distance from screen in cm

# Open the display window:
win = visual.Window([500, 500], allowGUI=False, monitor=screen,
                    units='deg', fullscr=not debugging, color=darklevel)

# Make a dummy message
message = visual.TextStim(win, units='norm', pos=[0, 0], height=0.07,
                          alignVert='center', alignHoriz='center',
                          text='', color=0.0)

# Make a white stimulus that covers the whole screen
flash = visual.GratingStim(win, tex='none', mask='none',
                           size=2, units='norm', color=1)

# Make a fixation cross
fixation = visual.GratingStim(win, tex='sqr', mask='cross', sf=0, size=0.3,
                              pos=[0, 0], color=-0.5, autoDraw=False)


# Open Tobii and activate
tracker = None
message.text = "Configuring..."
message.draw()
win.flip()
print("Opening eye tracker connection...")
tracker = tobiicontroller(win)
tracker.waitForFindEyeTracker()  # this scans the network
tracker.activate(tobiiid)  # this opens the tobii connection
print("Confirming eyes are present...")
tracker.findEyes()  # this mirrors the eyes on the screen
print("Calibrating....")
calibrated = False
while not calibrated:
    outcome = tracker.doCalibration()
    if outcome is 'retry':
        pass
    elif outcome is 'abort':
        raise KeyboardInterrupt("You interrupted the script.")
    elif outcome is 'accept':
        calibrated = True

# Open the parallel port
outport = parallel.ParallelPort()  # opens port at default address, LPT1
outport.setData(0)  # set all pins to low to start with


# Define a trial function
def trial(trialno):
    # Set directory for data storage
    tracker.setDataFile(datadir + 'trial %03d.csv' % (trialno))

    if event.getKeys(keyList=['escape']):
        raise KeyboardInterrupt("You interrupted the script manually.")
    # wait until the eyes are fixated and detected
    message.text = "Detecting eye fixation..."
    message.pos = (-1, -1)
    message.draw()
    fixation.draw()
    win.flip()
    tracker.waitForFixation(fixationPoint=fixation.pos)

    # calculate how much to wait before
    prewait = preflash + prejitter * np.random.rand()  # min wait plus jitter
    prewait -= prewait % (1 / screenrate)  # trim time to match framerate

    tracker.startTracking()

    # make dark and wait
    fixation.draw()
    win.flip()
    core.wait(prewait)
    # flash
    flash.draw()
    win.flip()
    trigger('flash start')
    core.wait(flashduration - 0.5 / screenrate)
    # set dark again
    fixation.draw()
    win.flip()
    trigger('flash end')
    core.wait(postflash - 0.5 / screenrate)
    tracker.stopTracking()
    # short break so subject can blink
    win.flip()
    core.wait(breaktime)


# Define an instruction function
def instruct(displaystring):
    message.text = displaystring
    message.draw()
    win.flip()
    event.waitKeys(keyList=['space'])


def trigger(triggevent):
    outport.setData(triggvalues[triggevent])  # set pins high
    tracker.recordEvent(triggevent)  # send event to tobii
    core.wait(0.001)  # wait so eeg picks it up
    outport.setData(0)  # set pins low again

# Give participant instructions
instruct("We will now test your eyes' response to changes in lightness. "
         "Please focus your eyes on the centre of the screen whenever the "
         "cross appears in the middle of the screen."
         "\n\nPress [space] to continue.")
instruct("You will see sudden changes in the brightness of the monitor. "
         "Please keep your eyes fixated on the centre of the screen even "
         "when they occur. Please also try not to blink while the fixation "
         "cross is on the screen."
         "\n\nPress space to begin.")
# Run trials
try:
    # Run one trial
    for trialno in range(n):
        trial(trialno)
finally:
    tracker.destroy()
    win.close()
