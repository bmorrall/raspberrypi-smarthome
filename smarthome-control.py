#!/usr/bin/env python

"""
  Author: Ben Morrall

  Script to setup Raspberry Pi as Smarthome Daemon
"""

import fauxmo
import logging
import time
from phue import Bridge
from threading import Thread
import soco

from debounce_handler import debounce_handler

logging.basicConfig(level=logging.INFO)

# Connect to the Hue Bridge
hue_bridge = Bridge('10.0.1.2')
hue_bridge.connect()

# Stop all Sonos Speakers
class StopMusicTask(Thread):
    def run(self):
        logging.info("Pausing all speakers")
        for zone in soco.discover():
            logging.info("Stopping " + zone.player_name)
            zone.group.coordinator.pause()

class SetupReadingInBedTask(Thread):
    def run(self):
        logging.info("Setting Bedroom scene to Tropical twilight")
        hue_bridge = Bridge('10.0.1.2')
        hue_bridge.run_scene("Bedroom", "Tropical twilight")

class SetupBedroomLightingTask(Thread):
    def run(self):
        logging.info("Setting Bedroom scene to Dimmed")
        hue_bridge = Bridge('10.0.1.2')
        hue_bridge.run_scene("Bedroom", "Dimmed")

class device_handler(debounce_handler):
    TRIGGERS = {
        "Setup Reading in Bed": 50100
    }

    def trigger_reading_in_bed(self, state):
        if state == True:
            reading_in_bed = SetupReadingInBedTask()
            reading_in_bed.start()
            stop_music = StopMusicTask()
            stop_music.start()
        else:
            bedroom_lighting = SetupBedroomLightingTask()
            bedroom_lighting.start()

    def trigger(self, port, state):
        actions = {
            50100: self.trigger_reading_in_bed
        }
        actions[port](state)

    def act(self, client_address, state, name):
        print "State", state, "on", name, "from client @", client_address
        self.trigger(self.TRIGGERS[str(name)], state)
        return True

if __name__ == "__main__":
    # Startup the fauxmo server
    fauxmo.DEBUG = True
    p = fauxmo.poller()
    u = fauxmo.upnp_broadcast_responder()
    u.init_socket()
    p.add(u)

    # Register the device callback as a fauxmo handler
    d = device_handler()
    for trig, port in d.TRIGGERS.items():
        fauxmo.fauxmo(trig, u, p, None, port, d)

    # Loop and poll for incoming Echo requests
    logging.debug("Entering fauxmo polling loop")
    while True:
        try:
            # Allow time for a ctrl-c to stop the process
            p.poll(100)
            time.sleep(0.1)
        except Exception, e:
            logging.critical("Critical exception: " + str(e))
            break
