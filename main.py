# coding: utf-8
from twistedinput.device import EventDevice
from twistedinput.protocol import EventProtocol, EventSniffer
from twistedinput.factory import InputEventFactory
from twistedinput.mapping import GamepadEventMapping, BaseJoystickMapping, BaseEventMapping
from twistedinput.defines import *
from twisted.internet import reactor

from construct import *

import socket

PlayerKeyPacket = Struct("PlayerKeyPacket",
    ULInt8("gameid"),
    Magic("I"),
    BitStruct("player2",
              Flag("xp"),
              Flag("xn"),
              Flag("yp"),
              Flag("yn"),
              Flag("x"),
              Flag("y"),
              Flag("a"),
              Flag("b"),
              ),
    BitStruct("player1",
              Flag("xp"),
              Flag("xn"),
              Flag("yp"),
              Flag("yn"),
              Flag("x"),
              Flag("y"),
              Flag("a"),
              Flag("b"),
              ),
)

#pad_device = u"/dev/input/by-id/usb-©Microsoft_Corporation_Controller_136DB16-event-joystick"
pad_device_1 = "/dev/input/event0"
pad_device_2 = "/dev/input/event1"

class Xbox360EventMapping(BaseEventMapping):

    def getKeyMapping(self):
        return {
            BTN_A           : "buttonA",
            BTN_B           : "buttonB",
            BTN_X           : "buttonX",
            BTN_Y           : "buttonY",
            0x0010          : "buttonLeft",

            BTN_TRIGGER     : "button1",
            BTN_THUMB       : "button2",
            BTN_THUMB2      : "button3",
            BTN_TOP         : "button4",
            BTN_TOP2        : "triggerLeft1",
            BTN_PINKIE      : "triggerRight1",
            BTN_BASE        : "triggerLeft2",
            BTN_BASE2       : "triggerRight2",
            BTN_BASE3       : "button9",
            BTN_BASE4       : "button10",
            BTN_BASE5       : "buttonJoystickLeft",
            BTN_BASE6       : "buttonJoystickRight",
            BTN_MODE        : "buttonXbox",
        }

    def getAbsMapping(self):
        return {
            ABS_X           : "joystickLeftX",
            ABS_Y           : "joystickLeftY",
            ABS_Z           : "joystickRightX",
            ABS_RZ          : "joystickRightY",
            ABS_HAT0X       : "dpadX",
            ABS_HAT0Y       : "dpadY"}

class Players(object):
    def __init__(self):
        self.player1=KeyStatus(1)
        self.player2=KeyStatus(2)

    def build(self):
        return PlayerKeyPacket.build(
                Container(gameid=255,
                          player1=Container(xp=self.player1.xp,
                                          yp=self.player1.yp,
                                          xn=self.player1.xn,
                                          yn=self.player1.yn,
                                          a=self.player1.a,
                                          b=self.player1.b,
                                          x=self.player1.x,
                                          y=self.player1.y
                          ),
                          player2=Container(xp=self.player2.xp,
                                          yp=self.player2.yp,
                                          xn=self.player2.xn,
                                          yn=self.player2.yn,
                                          a=self.player2.a,
                                          b=self.player2.b,
                                          x=self.player2.x,
                                          y=self.player2.y
                          ),
                )
        )


class KeyStatus(object):
    def __init__(self, player_id):
        self.player_id = player_id
        self.xp=False
        self.xn=False
        self.yp=False
        self.yn=False
        self.a=False
        self.b=False
        self.x=False
        self.y=False



    def __str__(self):
        return str("{} -> xp {} xn {} yp {} yn {} a {} b {} x {} y {} ".format(self.player_id,
                                                                         self.xp,
                                                                         self.xn,
                                                                         self.yp,
                                                                         self.yn,
                                                                         self.a,
                                                                         self.b,
                                                                         self.x,
                                                                         self.y))

HOST="192.168.1.106"
PORT=4242

class MySender(object):
    def __init__(self):
        self.status = Players()

        self.sock = socket.socket(type=socket.SOCK_DGRAM)
        self.sock.connect((HOST, PORT))
        self.sock.setblocking(0)

    def send(self):
        # self.sock.send(self.status.)
        # print(str(self.status.player1))
        # print(str(self.status.player2))
        try:
            reactor.callLater(0.0, self.sock.send, self.status.build() )
            # self.sock.send(self.status.build())
        except socket.error as e :
            print(e)


class MyGamepad(EventProtocol):

    def __init__(self, sender, player, *args, **kwargs):

        self.sender = sender
        self.player = self.sender.status.player1 if player == 1 else self.sender.status.player2
        self.player_id = player

        EventProtocol.__init__(self, *args, **kwargs)

        print("Init gamepad for player {} ({})".format(self.player_id, self.player))

        # self.status = Players()


    def send(self):
        self.sender.send()
        # reactor.callLater(0.0, self.send, None)

            

    def buttonA(self, event):
        print("button A: {}".format(event.value))
        self.player.a = event.value != 0x0
        self.send()

    def buttonB(self, event):
        print("button B: {}".format(event.value))
        self.player.b = event.value != 0x0
        self.send()

    def buttonX(self, event):
        print("button X: {}".format(event.value))
        self.player.x = event.value != 0x0
        self.send()

    def buttonY(self, event):
        print("button Y: {}".format(event.value))
        self.player.y = event.value != 0x0
        self.send()

    def buttonXbox(self, event):
        print("button XBOX: {}".format(event.value))
        if event.value == 0x1:
            self.player.xp = True
            self.player.xn = True
            self.player.yp = True
            self.player.yn = True
            self.player.a = True
            self.player.b = True
            self.player.x = True
            self.player.y = True
        else:
            self.player.xp = False
            self.player.xn = False
            self.player.yp = False
            self.player.yn = False
            self.player.a = False
            self.player.b = False
            self.player.x = False
            self.player.y = False

        self.send()



    def dpadX(self, event):
        # print("dpadX: {}".format(event))
        if event.value == 0x0 :
            self.player.xp = False
            self.player.xn = False
        elif event.value == 0x1:
            self.player.xp = True
            self.player.xn = False
        else:
            self.player.xp = False
            self.player.xn = True
        self.send()

    def dpadY(self, event):
        # print("dpadY: {}".format(event))
        if event.value == 0x0 :
            self.player.yp = False
            self.player.yn = False
        elif event.value == 0x1:
            self.player.yp = False
            self.player.yn = True
        else:
            self.player.yp = True
            self.player.yn = False
        self.send()

class EventSnifferCustom(EventProtocol):
    """
    tool for reading data. Developing purposes
    """

    def __init__(self, eventFactory):
        EventProtocol.__init__(self, eventFactory, None)

    def eventReceived(self, event):
        if event.type == 0x0000 :
            return
        print "event: %s" % (unicode(event),)

sender = MySender()

dev1=EventDevice(
    MyGamepad(sender, 1,
        InputEventFactory(),
        Xbox360EventMapping()),
    pad_device_1)

dev2=EventDevice(
    MyGamepad( sender, 2,
        InputEventFactory(),
        Xbox360EventMapping()),
    pad_device_2)

dev1.startReading()
dev2.startReading()

# EventDevice(
#     EventSnifferCustom(
#         InputEventFactory()
#         ),
#     pad_device).startReading()


reactor.run()
