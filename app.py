#!/usr/bin/env python3
"""BLE application for chili pad control. """
# -*- coding: utf-8 -*-
import array
import logging
from enum import Enum

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

from ble import (Advertisement, Agent, Application, Characteristic, Descriptor,
                 Service, find_adapter)
from chili_ctl import ChiliCtl

MainLoop = None
try:
    from gi.repository import GLib

    MainLoop = GLib.MainLoop
except ImportError:
    import gobject as GObject

    MainLoop = GObject.MainLoop

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)


mainloop = None

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotSupported"


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotPermitted"


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.InvalidValueLength"


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.Failed"


def register_app_cb():
    logger.info("GATT application registered")


def register_app_error_cb(error):
    logger.critical("Failed to register application: " + str(error))
    mainloop.quit()


class ChiliService(Service):
    """
    Dummy test service that provides characteristics and descriptors that
    exercise various API functionality.

    """

    SVC_UUID = "12634d89-d598-4874-8e86-7d042ee07ba7"

    def __init__(self, bus, index, controller):
        Service.__init__(self, bus, index, self.SVC_UUID, True)
        self.add_characteristic(ControlPointCharacteristic(bus, 0, self, controller))
        self.add_characteristic(
            TemperatureControlCharacteristic(bus, 1, self, controller)
        )


class ControlPointCharacteristic(Characteristic):
    """Characteristic to control various functionality such as power on or off.

    Attributes:
        uuid: characteristic uuid
        description: characteristic description
        value: characteristic value
        controller: controller interface
    """

    uuid = "4116f8d2-9f66-4f58-a53d-fc7440e7c14e"
    description = b"Chili pad controls"

    class State(list, Enum):
        """Control states

        Attributes:
            on: turn on
            off: turn off
        """

        OFF = bytes([0])
        ON = bytes([1])

    def __init__(self, bus, index, service, controller):
        Characteristic.__init__(
            self,
            bus,
            index,
            self.uuid,
            ["encrypt-read", "encrypt-write"],
            service,
        )

        self.value = self.State.OFF
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))
        self.controller = controller

    def ReadValue(self, options):
        logger.debug(f"Control point read: {self.value}")

        return self.value

    def WriteValue(self, value, options):
        print(value)
        if value == self.value:
            logger.debug("Control point write ignored, value not changed")
            return

        logger.debug(f"Control point write: {value}")
        if value == self.State.ON:
            self.controller.power_on()
            logger.debug("Control point power on")
            self.value = value
        elif value == self.State.OFF:
            self.controller.power_off()
            logger.debug("Control point power off")
            self.value = value
        else:
            logger.debug(f"Unknown control point value {value}")


class TemperatureControlCharacteristic(Characteristic):
    """Temperature control characteristic

    Attributes:
        uuid: characteristic uuid
        description: characteristic description
        controller: controller interface
        value: characteristic value
    """

    uuid = "322e774f-c909-49c4-bd7b-48a4003a967f"
    description = b"Set temperature in degrees F"

    def __init__(self, bus, index, service, controller):
        Characteristic.__init__(
            self,
            bus,
            index,
            self.uuid,
            ["encrypt-read", "encrypt-write"],
            service,
        )

        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))
        self.controller = controller
        self.value = self.controller.get_temp()

    def ReadValue(self, options):
        self.value = bytes([self.controller.get_temp()])
        logger.info(f"temperature read: {self.value}")

        return self.value

    def WriteValue(self, value, options):
        logger.info(f"temperature write: {value}")
        if value[0] > bytes([self.controller.max_temp])[0]:
            raise NotPermittedException
        if value[0] < bytes([self.controller.min_temp])[0]:
            raise NotPermittedException

        self.controller.set_temp(value)


class CharacteristicUserDescriptionDescriptor(Descriptor):
    """
    Writable CUD descriptor.
    """

    CUD_UUID = "2901"

    def __init__(
        self,
        bus,
        index,
        characteristic,
    ):
        self.value = array.array("B", characteristic.description)
        self.value = self.value.tolist()
        Descriptor.__init__(self, bus, index, self.CUD_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value


class ChiliAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_service_uuid(ChiliService.SVC_UUID)

        self.add_local_name("Chili-Ctl")
        self.include_tx_power = True


def register_ad_cb():
    logger.info("Advertisement registered")


def register_ad_error_cb(error):
    logger.critical("Failed to register advertisement: " + str(error))
    mainloop.quit()


AGENT_PATH = "/com/punchthrough/agent"


def main():
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    adapter = find_adapter(bus)

    if not adapter:
        logger.critical("GattManager1 interface not found")
        return

    adapter_obj = bus.get_object(BLUEZ_SERVICE_NAME, adapter)

    adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")

    # powered property on the controller to on
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    # Get manager objs
    service_manager = dbus.Interface(adapter_obj, GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(adapter_obj, LE_ADVERTISING_MANAGER_IFACE)

    advertisement = ChiliAdvertisement(bus, 0)
    obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")

    agent = Agent(bus, AGENT_PATH)

    app = Application(bus)
    controller = ChiliCtl()
    app.add_service(ChiliService(bus, 2, controller))

    mainloop = MainLoop()

    agent_manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")

    ad_manager.RegisterAdvertisement(
        advertisement.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )

    logger.info("Registering GATT application...")

    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=[register_app_error_cb],
    )

    agent_manager.RequestDefaultAgent(AGENT_PATH)

    mainloop.run()


if __name__ == "__main__":
    main()
