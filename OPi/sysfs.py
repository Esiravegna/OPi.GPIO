# -*- coding: utf-8 -*-
# Copyright (c) 2018 Richard Hull
# See LICENSE.md for details.

from contextlib import contextmanager
from os import access, W_OK
from time import sleep, time

from OPi.constants import HIGH, LOW, IN, OUT, \
    NONE, RISING, FALLING, BOTH

# Allow to wait up to 1 second for the file have the correct permissions
WAIT_PERMISSION_TIMEOUT = 1.

def wait_for_permissions(path):
    """
    Given the proper path, checks if we can use it.
    For this to workm, we'd need to crate a proer UDER file with this instructions:

    https://forum.armbian.com/topic/1851-rfc-make-armbian-more-iot-friendly/

    ```
    SUBSYSTEM=="input", GROUP="input", MODE="0660"
    SUBSYSTEM=="i2c-dev", GROUP="i2c", MODE="0660"
    SUBSYSTEM=="spidev", GROUP="spi", MODE="0660"
    SUBSYSTEM=="bcm2835-gpiomem", GROUP="gpio", MODE="0660"

    SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c '\
        chown -R root:gpio /sys/class/gpio && chmod -R 770 /sys/class/gpio;\
        chown -R root:gpio /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio;\
        chown -R root:gpio /sys$devpath && chmod -R 770 /sys$devpath\
    '"

    KERNEL=="ttyAMA[01]", PROGRAM="/bin/sh -c '\
        ALIASES=/proc/device-tree/aliases; \
        if cmp -s $ALIASES/uart0 $ALIASES/serial0; then \
            echo 0;\
        elif cmp -s $ALIASES/uart0 $ALIASES/serial1; then \
            echo 1; \
        else \
            exit 1; \
        fi\
    '", SYMLINK+="serial%c"

    KERNEL=="ttyS0", PROGRAM="/bin/sh -c '\
        ALIASES=/proc/device-tree/aliases; \
        if cmp -s $ALIASES/uart1 $ALIASES/serial0; then \
            echo 0; \
        elif cmp -s $ALIASES/uart1 $ALIASES/serial1; then \
            echo 1; \
        else \
            exit 1; \
        fi \
    '", SYMLINK+="serial%c" 
    ```
    in something like
    ```
    /etc/udev/rules.d/99-com.rules
    ```
    or the like, and the user running GPIOI should be part of the gpio group, which should exists beforehand of course.
    """
    start_time = time()
    while not access(path, W_OK) and time() - start_time < WAIT_PERMISSION_TIMEOUT:
        # Let's wait up to a second with 1/05th interval
        sleep(0.05)


@contextmanager
def value_descriptor(pin, mode="r"):
    path = "/sys/class/gpio/gpio{0}/value".format(pin)
    wait_for_permissions(path)
    with open(path, mode) as fp:
        yield fp


def export(pin):
    path = "/sys/class/gpio/export"
    wait_for_permissions(path)
    with open(path, "w") as fp:
        fp.write(str(pin))


def unexport(pin):
    path = "/sys/class/gpio/unexport"
    wait_for_permissions(path)
    with open(path, "w") as fp:
        fp.write(str(pin))


def direction(pin, dir):
    assert dir in [IN, OUT]
    path = "/sys/class/gpio/gpio{0}/direction".format(pin)
    wait_for_permissions(path)
    with open(path, "w") as fp:
        if dir == IN:
            fp.write("in")
        else:
            fp.write("out")


def input(pin):
    with value_descriptor(pin) as fp:
        value = fp.read()
        if value.strip() == str(LOW):
            return LOW
        else:
            return HIGH


def output(pin, value):
    str_value = "1" if value else "0"
    with value_descriptor(pin, "w") as fp:
        fp.write(str_value)


def edge(pin, trigger):
    assert trigger in [NONE, RISING, FALLING, BOTH]
    path = "/sys/class/gpio/gpio{0}/edge".format(pin)
    opts = {
        NONE: "none",
        RISING: "rising",
        FALLING: "falling",
        BOTH: "both"
    }
    wait_for_permissions(path)
    with open(path, "w") as fp:
        fp.write(opts[trigger])
