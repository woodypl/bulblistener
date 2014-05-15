Lighting notification and interaction system
============================================

This is a getting-started documentation for the system developed as a part of the MSci project by Paweł Drewniak, School of Computing Science at the University of Glasgow in AY 2013/14.

The system consists of several parts:

***hardware***:

* [LPD8806] LED strips
* [Philips Hue] smart light bulbs
* [mbed] microcontroller board with a [WiFly] module to control the strips
* [Raspberry Pi] acting as a server and, optionally, driving the strips

***software***:

 * [FlyLEDs] strip controller running on mbed
 * [bulblistener] a Python daemon receiving notifications and dispatching light events to the hardware
 * [ledmockup], a low-resolution and low-density LED display emulator running on any PyGame-supported platform (including Android)
 * [taglistener], a minimal Android app scanning NFC tags and passing them to [bulblistener]
 * [bulbaction], an Android app passing notifications and calendar data to the [bulblistener] and allowing manual control of a LED strip
 * [skypebulb], a simple Python daemon retrieving Skype status of chosen contacts and projecting them on Philips Hue bulbs

At the moment, there are certain hard-coded values in the code that need to be changed to suit your needs before the system can be made operational. Initial provisions for automatic device discovery have been implemented, though.
All the communication between system parts is achieved via HTTP (with the automatic discovery part using UDP broadcasts).

Getting started
---------------

### 1. Preparing the LED strip control board
If you wish to make your own board, you will need the following components:

* mbed NXP [LPC1768] microcontroller
* Microchip (Roving Networks) [RN-171-XV] WiFly module
* appropriate sockets for the above, including Xbee socket and breakout board (the WiFly module has non-standard pin spacing)
* reliable power supply - you need 5V with 120mA per segment (2 LEDs)
* sockets, connectors, jump wires as appropriate

Your requirements may vary, but just to give you an idea, I used:
* 7805CV for powering the strip
* 7805 for powering the LPC1768 and WiFly
* 0.33uF capacitors at the input to the regulators
* 10uF capacitors at the output (use 0.1uF or greater, as per the application note)
* Molex connectors for the strips and power
* Ribbon cables to connect the strips

It's best to use separate PSUs for the control logic and for the strip itself - this way you increase the chances your setup will be stable and not subject to any issues cause by oddly-behaving strips.
In any case, make sure you supply clean power, well within the requirements. As the strips use SPI-like protocol, you also need to make sure that the microcontroller and the strip share a common ground - otherwise uneven ground levels will prevent the strip from operating!

I used voltage regulators 7805 (up to 1A output current) and 7805CV (up to 1.5A), with appropriate smooth-out capacitors added as per the respective application notes. Please also note that the regulators tend to get quite hot - plan your circuit board design well in advance and take the possible need for a heatsink into account. Always read application notes and datasheets carefully. For instance, note the minimal input voltage for 7805 series (7.3V).
There was another PSU setup that was also recommended to me, but I have not had a chance to test it - you may want to have a look at a [buck-boost converter](http://en.wikipedia.org/wiki/Buck%E2%80%93boost_converter).
When soldering, make sure that the wiring to and from the strip is rock solid - even a slightly loose connection can affect the colours on the strip!

The mbed website has excellent documentation on the [LPC1768], [WiFly](https://mbed.org/components/Roving-Networks-WiFly-RN-171-XV/) and even the [strips](https://mbed.org/users/ehbmbed2/code/LPD8806/file/6ebd3ac910b6/LPD8806.cpp).
Should you follow the steps described there, you should have no problems wiring the kit up.

### 2. Compiling the firmware image
The [FlyLEDs] software was written in C++, making use of the mbed libraries available. The libraries were modified and a few bugs fixed, so please use the whole package supplied. It is easiest to use the [mbed online compiler](https://mbed.org/compiler/), as it provides single-click compilation and does not require any special setup. Should you wish to work locally, you are on your own to install a toolchain and an IDE - I have not succeeded in doing so. Otherwise, just import the FlyLEDs zip file into the compiler.

You need to make the following adjustments to the code:

* set `ledcount1` and `ledcount2` to the respective strip lengths
* set `essid` and `psk` to match the Wi-Fi network you'll connect to

The rest is optional - if you wish to enable HTTP registration, you need to alter the URL and uncomment the respective bits of code. Bear in mind that the WiFly module broadcasts keepalive messages by default on UDP port 55555 anyway.

Once you hit _compile_, you'll get a .bin file that you need to upload to the microcontroller. It's as simple as drag-and-drop. Reset the board and you should be ready to go. See the [mbed website](http://www.mbed.org) for more details.

### 3. Preparing the notification router
You'll need a device connected to the same network as your strip. I used a laptop initially and switched to a Raspberry Pi later on. Anything that can run Ethernet and Python 2 will do. 

Using Linux terminal:

```
git clone https://github.com/woodypl/bulblistener/
cd bulblistener
vi bulbserver.py
```

Naturally, you need to make some changes to this proof-of-concept code too.
Change the values given for the strips in _handle_tag_ and _do_POST_ methods to match the values of your strip boards. The default behaviour for this script is to act as a Pizza-o-meter for the _handle_tag_ method and set the given values for the other strip in the _do_POST_ method. There is also Skype status projection available - change the first two lines of _updateskype_ method accordingly.
Once the changes have been made, run ```python bulbserver.py```. This should make the script listen for incoming connections. For best results, run it in [GNU screen](http://www.gnu.org/software/screen/) or a similar setup.
You will notice that the script logs every request to the console and that some of the interaction is saved to text files.

### 4. Preparing the BulbAction Android app
_BulbAction_ is an Android app that uses the Android calendar to determine hourly availability during the day and sends this information to the notification router.
This is how the _AvailaStrip_ part of the system works - the calendar entries are converted to three colours, depending on availability being 60 minutes, 30 minutes or less within an hour. The user has an option to fine-tune the settings of particular LEDs. Additionally, this part of software has a _NotificationListener_ service running in the background, passing all Android notifications on to the router.

You will need [Eclipse with Android Development Toolkit](http://developer.android.com/tools/sdk/eclipse-adt.html). Android Studio might work, but it has not been tested.

```
git clone https://github.com/woodypl/bulbaction/
```

In Eclipse, create a new Android project, and point it at the source directory. You will need to change the *final string* `URL` to point at the notification router (default port 8000).
Following that, you should be ready to run the app on an Android device. Bear in mind that you should ideally use Android 4.4.2 or higher (KitKat) to access all extra notification data. Lower versions are untested.

### 5. Preparing the NFC tag listener
As part of the _Pizza-o-meter_, a demo of the interest registration idea, I used an NFC-enabled mobile phone to scan people's ID cards. I developed a simple Android activity that would keep the phone on and scan for any NFC cards in the vicinity. Upon detecting one, it would pass its ID on to the notification router.

```
git clone https://github.com/woodypl/taglistener/
```

As before, use Eclipse with ADT. Change the _URL_ constant to match the notification router's IP.

### 6. Running the low-resolution display - ledmockup
_LedMockup_ is written in [PyGame], and thus will run on any platform supporting it 
To see what it does locally, I'd recommend you to take a look at its [local version](https://github.com/woodypl/ledmockup). Otherwise, you can skip straight to the process of deploying it on an Android device (I used a Motorola Xoom). It would run on pretty much any Android version, but I'd suggest using at least 4.0 so that the immersive display feature (the picture covering the whole screen) would work well.

The setup process for this is quite complicated:

1. Retrieve the repositories
```
git clone https://github.com/woodypl/ledmockup/
git clone https://github.com/renpy/rapt.git
cd rapt
git submodule init
git submodule update
```
2. Download the Android NDK - you need version 8c:
```
wget http://dl.google.com/android/ndk/android-ndk-r8c-linux-x86.tar.bz2
tar xvjf android-ndk-r8c-linux-x86.tar.bz2
```
3. Install the Android SDK and Apache Ant:
```
python android.py installsdk
```
4. Apply the patch provided and start the build process
```
patch < ../ledmockup/android/rapt-ledmockup.patch
./build_pgs4a.sh
```
Watch out for errors. You might need to install some development libraries, YMMV depending on the system you use.
5. Create an Android project using pgs4a
```
cd dist/pgs4a
cp -R ../../../ledmockup/android .
#connect your device in USB debug mode now
python android.py build install
```

This should result in an Android APK being compiled and installed onto your device. You can now run _LedMockup_ on the device - it will accept any images directed at it and display them.

###7. Skype setup
The Skype Python module requires [skype4py] and a Skype client running. This is not a nice deployment - you need an x86/x86_64 Linux machine with an X server running (it could be headless, though).
This part of the project was standalone and did not require the use of notification router. You need to 
You need to install [skype4py] and [phue] as per their documentation and have Skype up and running.

```
git clone https://github.com/woodypl/wavelight
cd wavelight
```

Now edit `skype.py` and replace the `BRIDGE_IP`, `BRIDGE_USERNAME` and all `HANDLE` variables with your own ones. Please note that the user you are running Skype as should have the users whose Skype statuses you are checking in its contact list.
You should also replace the bulb names if you are using a different Hue kit than I.

Then just run

```
DISPLAY=:0 python skype.py
#your X display number may vary
```

and you should be prompted by the Skype client with an API access request. After acceptance, the script will run as a daemon, reacting to Skype status changes.

_Additional information_: There is a provision for integrating the Skype status with the notification router. As at the time this project was done both systems were on isolated networks, it ended up being a dirty hack: the user in the `WWWHANDLE` variable has their status written to a file, which is then served over Web and available for periodic polling by the notification router (see the _updateskype_ method there).

Alternative setup
-----------------

If you wish, you can use a Raspberry Pi to drive and even power the LED strips. You need to be current-aware though - make sure you calculate how many LEDs you can afford to light up and at what brightness!
You need Raspberry Pi with enable hardware SPI support. 

1. First of all, check out the [RPi-LPD8806] library which also explains how to connect the strip to the Pi.
2. Install the library as per the documentation.
3. 
```
git clone https://github.com/woodypl/ledstrip
cd ledstrip
python ledstrip.py
```

The software resembles the firmware part of the control board and speaks the same protocol. Just point the notification router at the Pi's IP and you are ready to go.

Protocol description
--------------------

The strip control board (and the _ledstrip_ software) speak a primitive, character-based protocol, allowing for control of the strip. The data are passed through a TCP socket.

* Each command has a fixed width of 8 bytes
* First byte (`[0]`)has a value of `\xff` (255)
* Second byte (`[1]`)determines the command:
 * **`!`** _updates_ (flushes) the LED values to the strip
 * **`=`** _sets_ a particular LED to a given value:
       * `[2]` is the strip number (for a multi-strip board)
       * `[3][4]` are the LED number (10*`[3]`+`[4]`)
       * `[5]`, `[6]`, `[7]` are the RGB components 
 * **`>`** toggles the _breathing_ of a particular LED
       * `[2]` is the strip number (for a multi-strip board)
       * `[3][4]` are the LED number (10*`[3]`+`[4]`)

[LPD8806]:http://www.adafruit.com/products/306
[Philips Hue]:http://meethue.com/
[mbed]:http://www.mbed.org
[Raspberry Pi]:http://www.raspberrypi.org/
[FlyLEDs]:https://github.com/woodypl/ledstrip/blob/master/FlyLEDs.zip
[bulblistener]:https://github.com/woodypl/bulblistener
[ledmockup]:https://github.com/woodypl/ledmockup
[taglistener]:https://github.com/woodypl/taglistener
[bulbaction]:https://github.com/woodypl/bulbaction
[skypebulb]:https://github.com/woodypl/wavelight/blob/master/skype.py
[LPC1768]:https://mbed.org/platforms/mbed-LPC1768/
[WiFly]:http://www.microchip.com/wwwproducts/Devices.aspx?product=RN171XV
[RN-171-XV]:https://mbed.org/components/Roving-Networks-WiFly-RN-171-XV/
[PyGame]:http://www.pygame.org/news.html
[RPi-LPD8806]:https://github.com/adammhaile/RPi-LPD8806
[skype4py]:https://github.com/awahlig/skype4py
[phue]:https://github.com/studioimaginaire/phue


