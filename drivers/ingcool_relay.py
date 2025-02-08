#!/usr/bin/python3
"""Control Raspberry Pi relay board. """

from enum import Enum

try:
    import RPi.GPIO as GPIO
except ImportError:
    import Mock.GPIO as GPIO


class IngcoolRelayChannel(int, Enum):
    """Relay channels for Ingcool Raspberry Pi relay board.
    Note: Channels are physical pin numbers on the board using the board
    numbering system.

    Attributes:
        CH1: relay channel 1
        CH2: relay channel 2
        CH3: relay channel 3
    """

    CH1 = 37
    CH2 = 38
    CH3 = 40


class IngcoolRelay:
    """Control Ingcool Raspberry Pi relay board.

    Attributes: 
        enabled_channels: relay channels that are currently on.
    """

    def __init__(self) -> None:
        GPIO.setmode(GPIO.BOARD)
        self.enabled_channels = {}
        for chan in IngcoolRelayChannel:
            GPIO.setup(chan, GPIO.OUT)
            self.enabled_channels[chan] = False

    def on(self, channel: IngcoolRelayChannel) -> None:
        """Turn relay channel on (closed circuit).

        Args:
            channel: relay channel to enable
        """
        GPIO.output(channel, GPIO.LOW)
        self.enabled_channels[channel] = True

    def all_on(self) -> None:
        """Turn all relay channels on."""
        for chan in IngcoolRelayChannel:
            GPIO.output(chan, GPIO.LOW)
            self.enabled_channels[chan] = True

    def is_on(self, channel: IngcoolRelayChannel) -> bool:
        """Test if a relay channel is already on.

        Args:
            channel: relay channel to test

        Returns: true if channel is on, false if it's off
            
        """
        return self.enabled_channels[channel]

    def off(self, channel: IngcoolRelayChannel) -> None:
        """Turn relay channel off (open circuit).

        Args:
            channel: relay channel to disable
        """
        GPIO.output(channel, GPIO.HIGH)
        self.enabled_channels[channel] = False

    def all_off(self) -> None:
        """Turn all relay channels off"""
        for chan in IngcoolRelayChannel:
            GPIO.output(chan, GPIO.HIGH)
            self.enabled_channels[chan] = False

    def __del__(self):
        self.all_off()
        GPIO.cleanup()
