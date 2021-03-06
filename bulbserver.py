#!/usr/bin/env python2
import sys
import logging
import socket
import threading
import time
from datetime import datetime
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from shutil import copyfileobj
#from draw import Mockup
#from urllib import parse
#from apscheduler.scheduler import Scheduler
import urlparse as parse
from urllib import urlopen
#import pygame
import json
import urllib2
import simplejson
from PIL import Image
from StringIO import StringIO

strips = []
ledmockups = []
broadcastlisten = True

class StripHandler:

    ip = ""
    port = 0
    cnt = 0
    #sched = Scheduler()

    def __init__(self,ip,port,cnt):
        self.ip = ip
        self.port = port
        self.cnt = cnt
	#StripHandler.sched.start()
    
    #@sched.cron_schedule(hour='9-17')
    def update_breathing(self):
        t = datetime.now().hour
	if (t >= 10 and t <= 16):
		self.breathe(8-(t-10))
		self.breathe(8-(t-9))
	elif (t == 17):
		self.breathe(0)
	elif (t == 9):
		self.breathe(7)
    
    def __str__(self):
        return "LED Strip @{0}".format(self.ip)
    
    def setled(self,port, num,r,g,b):
        self.socket = socket.socket()
        self.socket.connect((self.ip, self.port))
        self.socket.sendall(b'\xff'+str.encode('={0}{1:02d}{2:c}{3:c}{4:c}'.format(port, num, r, g, b)))
        self.socket.close()

    def setstrip(self, port, arr):
        data = b''
        self.socket = socket.socket()
	self.socket.connect((self.ip, self.port))
	for i in range(0, len(arr)):
            #data += b'\xff'+str.encode('={0}{1:02d}{2:c}{3:c}{4:c}'.format(port, i, arr[i][0], arr[i][1], arr[i][2]))
	    self.socket.sendall(b'\xff'+str.encode('={0}{1:02d}{2:c}{3:c}{4:c}'.format(port, i, arr[i][0], arr[i][1], arr[i][2])))
	    time.sleep(0.05)
        #self.socket.sendall(data) #Does not work at present - sending too fast, receiver can't cope.
        self.socket.close()

    def breathe(self, port, pos):
        self.socket = socket.socket()
        self.socket.connect((self.ip, self.port))
        self.socket.sendall(b'\xff'+str.encode('>{0}{1:02d}000'.format(port, pos)))
        self.socket.close()


    def show(self, port):
        self.socket = socket.socket()
        self.socket.connect((self.ip, self.port))
        self.socket.sendall(b'\xff!'+str.encode(str(port))+b'!!!!!')
        self.socket.close()

class ServerHandler(SimpleHTTPRequestHandler):

    interest = []
    strips = []
    avatars = {} #Key: IP, Value: avatar binary data
    options = {} #Key: IP, Value: List [now, weather, project, name]

    def __init__(self,request,client_address,server):
        #self.mockup = Mockup()
        #pygame.init()
        #self.window = pygame.display.set_mode((848, 480))#, pygame.FULLSCREEN)
        SimpleHTTPRequestHandler.__init__(self, request,client_address,server)


    def dispatch_notification(self, remove=False):
        #We're still in the request handler, let's make use of what's available to us
        res = parse.urlparse(self.path)
        params = dict(parse.parse_qsl(res.query))
	action = "Removed" if remove else "New"
	client = self.client_address[0] #IP

	if not self.avatars.has_key(self.client_address[0]) and params.has_key('account'):
		picasainfo = urllib2.urlopen("http://picasaweb.google.com/data/entry/api/user/{0}?alt=json".format(params['account']))
		avatarurl = simplejson.loads(picasainfo.read())['entry']['gphoto$thumbnail']['$t']
		self.avatars[self.client_address[0]] = urllib2.urlopen(avatarurl).read()
		print("Adding avatar for account {0} and IP {1}".format(params['account'], self.client_address[0]))
	
	with open("notifications.log", "a") as logfile:
       	    try:
	        logfile.write("{4} {0}: {1} notification #{2} from {3}\n".format(client, action, params['id'], params['pkg'], time.time()))
	    except:
	        logfile.write("{4} {0}: {1} unknown notification format. {2}".format(client,action,params,time.time()))


    def handle_tag(self, tag):
	strip = StripHandler('10.10.10.31', 80, 12)
        if tag not in self.interest:
            self.interest.append(tag)
	    #get green and flash the strip with it
            arr = [ServerHandler.getcolor(1) for i in range(0,strip.cnt)]
	    strip.setstrip(0, arr)
            strip.show(0)
        else:
            arr = [ServerHandler.getcolor(3) for i in range(0,strip.cnt)]
            strip.setstrip(0, arr)
            strip.show(0)
	time.sleep(1)
        ratio = len(self.interest)/(1.0*strip.cnt)
	color = 0
	if ratio < 0.2:
	    color = 3
        elif ratio < 0.5:
            color = 2
        else:
            color = 1
        arr = [ServerHandler.getcolor(color) for i in range (0, len(self.interest))]
	arr += [ServerHandler.getcolor(0) for i in range (len(self.interest), strip.cnt)]
        strip.setstrip(0, arr)
        strip.show(0)
        print("Interest for {0} is now {1}".format(tag, self.interest))
        with open("pizza.txt", "a") as logfile:
            logfile.write("{0}: PizzaStrip interaction: {1}\n".format(datetime.now(), tag))


    @staticmethod
    def get_skype_status(username):
        #res = urlopen('http://mystatus.skype.com/{0}.num'.format(username))
        res = urlopen('http://www.dcs.gla.ac.uk/L311_D/ben.txt')
	status = str(res.read())
        res.close()
        return status

    @staticmethod
    def get_weather(city="Glasgow"):
        """Get weather data and convert its format to a tuple (temperature, rain, cloud)"""
        weather = json.loads(urlopen('http://api.openweathermap.org/data/2.5/weather?units=metric&q={0}'.format(city)).read())
        temp = weather['main']['temp']
        try:
            rain = weather['rain']['3h']
            cond = weather['weather'][0]['id']
        except KeyError:
            rain = 0
            cond = 0
        clouds = weather['clouds']['all']

        if temp < 8:
            temp = (0,0,127)
        elif temp < 13:
            temp = ServerHandler.getcolor(1)
        else:
            temp = ServerHandler.getcolor(3)

        if rain < 3:
            rain = ServerHandler.getcolor(1)
        elif rain < 10:
            rain = ServerHandler.getcolor(2)
        else:
            rain = ServerHandler.getcolor(3)

        if clouds < 30:
            clouds = ServerHandler.getcolor(1)
        elif clouds < 70:
            clouds = ServerHandler.getcolor(2)
        else:
            clouds = ServerHandler.getcolor(3)

        return (temp, rain, clouds)

    def do_GET(self):
        #logging.error(self.headers)
        #SimpleHTTPRequestHandler.do_GET(self)
        res = parse.urlparse(self.path)
        params = parse.parse_qsl(res.query)
        if res.path == '/skype': #id and status
            pass
        elif res.path == '/registerstrip':
            found = False
            for strip in self.strips:
                if strip.ip == self.client_address[0]:
                    found = True
                    print("Strip already registered.")
            if not found:
                self.strips.append(StripHandler(self.client_address[0], 80, 20))
                print("Strip list updated: {0}".format(str(self.strips)))
        #self.log_request(200)
        self.send_response(200, "OK")
        self.end_headers()
        #self.wfile.close()

    @staticmethod
    def getcolor(num):
        num = int(num)
        if num == 0:
            return (0,0,0)
        elif num == 1:
            return (0,127,0)
        elif num == 2:
            return (127,80,0)
        elif num == 3:
            return (127,0,0)
        else:
            return (0,0,127)

    def do_POST(self):
        #logging.error(self.headers)
        res = parse.urlparse(self.path)
        params = parse.parse_qsl(res.query)
        if res.path == '/notify':
            self.dispatch_notification()
	elif res.path == '/denotify':
	    self.dispatch_notification(remove=True)
        elif res.path == '/nfctag':
            self.handle_tag(params[0][1]) #harcoded value of first query param
        elif res.path == '/availastrip':
            states = params[0][1][::-1] #string of values
            strip = StripHandler('127.0.0.1', 8001, 8)
            for i in range(0, strip.cnt):
               c = ServerHandler.getcolor(states[i]) 
               strip.setled(0, i, c[0], c[1], c[2])
               print("{0} {1} {2} {3}".format(i, c[0], c[1], c[2]))
            strip.show(0)
	    with open("rod.txt", "a") as logfile:
	        logfile.write("{0}: AvailaStrip interaction: {1} \n".format(datetime.now(), states))
        elif res.path == '/options':
            addr = self.client_address[0]
            self.options[addr] = [params[0][1], params[1][1], params[2][1], params[3][1]]
        #self.log_request(200)
        self.send_response(200, "OK")
        self.end_headers()


        length = int(self.headers.get('Content-Length', 0))
        if length > 0 and res.path != '/denotify':
            data = self.rfile.read(length)
	    self.rfile.close()
	    self.wfile.close()
	    if res.path == '/avatar':
	        self.avatars[self.client_address[0]] = data
	        return
	    im = Image.open(StringIO(data))
	    imsize = im.size
	    if self.avatars.has_key(self.client_address[0]):
	        av = Image.open(StringIO(self.avatars[self.client_address[0]]))
	        avsize = (imsize[0]/4, imsize[1]/4)
	        av = av.resize(avsize, Image.ANTIALIAS)
	        im.paste(av, (imsize[0]-avsize[0], imsize[1]-avsize[1], imsize[0], imsize[1]))
	    data = StringIO()
	    im.save(data, "PNG")
	    for addr in ledmockups:
	            	urllib2.urlopen("http://{0}:8000/undim".format(addr))
			urllib2.urlopen("http://{0}:8000".format(addr), data=data.getvalue())
	    #f.write(data)
            #f.close()
            #self.mockup.filename = 'test.png'
            #matrix = self.mockup.load_image()
            #self.mockup.draw_matrix(self.window, matrix, (self.mockup.radius, self.mockup.radius))
            #pygame.display.flip()
        else: #Denotify was called
		for addr in ledmockups:
			urllib2.urlopen("http://{0}:8000/dim".format(addr))
	#count = int(self.path[self.path.find('=')+1:])
        #self.mockup.draw_progress(self.window, count/5)
        #self.wfile.close()

def detectdevices():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 55555))

    while broadcastlisten:
        data, addr = sock.recvfrom(1024)
        #print("UDP Broadcast detected: ", data)
        if "LedMockup" in data and addr[0] not in ledmockups:
		print("Adding LedMockup @{0}".format(addr[0]))
		ledmockups.append(addr[0])
	#else:
	#	strips.append(StripHandler(addr, 80, 8))

def updateskype():
    while True:
	    strip = StripHandler('10.10.10.38', 80, 2)
	    status = ServerHandler.get_skype_status('skypebulb')
	    if status == "ONLINE":
		strip.setled(1, 0, 0, 127,0 )
	    elif status == "BUSY":
	        strip.setled(1, 0, 127, 0,0 )
	    elif status == "AWAY":
	        strip.setled(1, 0, 127, 80, 0 )
	    else:
		strip.setled(1, 0, 0, 0, 0 )
	    strip.show(1)
	    time.sleep(30)
	

if __name__ == "__main__":

    HandlerClass = ServerHandler
    ServerClass  = HTTPServer
    Protocol     = "HTTP/1.0"

    port = 8000
    server_address = ('0.0.0.0', port)

    HandlerClass.protocol_version = Protocol
    httpd = ServerClass(server_address, HandlerClass)
    sa = httpd.socket.getsockname()

    keepalive = threading.Thread(target=detectdevices)
    keepalive.start()

    #skypethread = threading.Thread(target=updateskype)
    #skypethread.start()
    
    print ("Serving HTTP on", sa[0], "port", sa[1], "...")
    try:
        httpd.serve_forever()
    except:
        broadcastlisten = False
