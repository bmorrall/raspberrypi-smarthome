#!/usr/bin/env python

"""
  Author: Ben Morrall

  Script to setup Raspberry Pi as Smarthome Daemon
"""

import fauxmo
import logging
import time
from phue import Bridge
import soco

from debounce_handler import debounce_handler

logging.basicConfig(level=logging.INFO)

# Connect to the Hue Bridge
hue_bridge = Bridge('10.0.1.2')
hue_bridge.connect()

class device_handler(debounce_handler):
    TRIGGERS = {
        "Setup Reading in Bed": 50100
    }

    def stop_all_music(self):
        # Stop all Sonos Speakers
        for zone in soco.discover():
            logging.info("Stopping " + zone.player_name)
            zone.group.coordinator.pause()

    def trigger(self, port, state):
        if state == True:
            hue_bridge.run_scene("Bedroom", "Tropical twilight")
            self.stop_all_music()
        else:
            hue_bridge.run_scene("Bedroom", "Dimmed")

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
