"""Test the Ingcool relay board for raspberry pi python driver. """

import time

from drivers.ingcool_relay import IngcoolRelay, IngcoolRelayChannel


def test_relay_on_off():
    """Test turning on and off each individual relay."""
    relay = IngcoolRelay()
    for chan in IngcoolRelayChannel:
        relay.on(chan)
        time.sleep(0.5)
        assert relay.is_on(chan) is True
        relay.off(chan)
        time.sleep(0.5)
        assert relay.is_on(chan) is False

def test_relay_all_on_off():
    """Test all on and all off of relay board."""
    relay = IngcoolRelay()
    relay.all_on()
    time.sleep(0.5)
    for chan in IngcoolRelayChannel:
        assert relay.is_on(chan) is True
    relay.all_off()
    time.sleep(0.5)
    for chan in IngcoolRelayChannel:
        assert relay.is_on(chan) is False
