"""NongoFit - response utilities.

This contains utilities for converting bytearray data into structured resposes.
"""

import enum


class ResponseTypes(enum.Enum):
    """Supported response types."""

    UNKNOWN = enum.auto()
    TREADMILL_STATE = enum.auto()


def _to_int(byte_values: bytearray):
    """Converts `byte_values` into a little-endian integer."""
    return int.from_bytes(byte_values, byteorder="little")


class TreadmillStateResponse:
    """Response containing the current state of the treadmill.

    Example sequence (with device type info stripped):

    02 a000 2c01 7100 1400 0000 00 0000 00 02 3100 310000009a630300b4003f
       PPPP IIII      DDDD      UU      EE    TTTT

    (P)ace
    (I)ncline
    (D)istance
    (T)imer
    P(U)lse
    Pulse (E)nabled
    """

    def __init__(self, raw_bytes: bytearray = None):
        self._raw_bytes = raw_bytes
        self.type = ResponseTypes.TREADMILL_STATE

        # Slices containing the locations of known data.
        self._slices = {
            "PACE": slice(1, 3),
            "INCLINE": slice(3, 5),
            "DISTANCE": slice(7, 9),
            "PULSE": slice(11, 12),
            "PULSE_ENABLED": slice(14, 15),
            # TODO: Add more info - this is 0x1 in 'normal' mode and '0x7' in
            # the settings menu (can't trigger other values).
            #'DISPLAY_MODE': slice(15, 16),
            "TIMER": slice(18, 20),
        }

        self.pace = self._extract_pace(raw_bytes)
        self.incline = self._extract_incline(raw_bytes)
        self.distance = self._extract_distance(raw_bytes)
        self.timer = self._extract_timer(raw_bytes)
        self.pulse = _to_int(raw_bytes[self._slices["PULSE"]])
        self.pulse_enabled = bool(_to_int(raw_bytes[self._slices["PULSE_ENABLED"]]))

    def debug_string(self):
        """Prints a representation suitable for logging/debugging."""
        masks = set()
        for data_slice in self._slices.values():
            masks.update(range(data_slice.start, data_slice.stop))

        # 'Erase' all bytes that are already known.
        masked_bytes = "".join(
            "  " if index in masks else f"{byte_:0>2x}"
            for index, byte_ in enumerate(self._raw_bytes)
        )

        spacer = " " * 4
        return (
            f"(TreadmillState){spacer}"
            f"{self.pace} mph{spacer}"
            f"{self.incline}% incline{spacer}"
            f"{self.distance:.3f} miles{spacer}"
            f"{self.timer:4} seconds{spacer}"
            f"Pulse:{self.pulse:>3} bpm{spacer}"
            f"{masked_bytes}"
        )

    def to_dict(self):
        """Surprise: this converts the response into a dictionary."""
        return {
            "pace": self.pace,
            "incline": self.incline,
            "distance": self.distance,
            "timer": self.timer,
        }

    def _extract_pace(self, byte_values: bytearray):
        """Pace is a two-byte value representing in kilometers-per-hour.

        Conversion:
          * Convert the bytes to a little-endian integer
          * Divide by 100 (stored as an integer / presented as a float)
          * Multiply by 0.621 to convert kilometers to miles
          * Round to one decimal
        """
        return round((_to_int(byte_values[self._slices["PACE"]]) / 100.0) * 0.621, 1)

    def _extract_incline(self, byte_values: bytearray):
        """Incline is a two-byte value representing the percentage incline.

        Conversion:
          * Convert the bytes to a little-endian integer
          * Divide by 100
        """
        return round((_to_int(byte_values[self._slices["INCLINE"]]) / 100.0), 1)

    def _extract_distance(self, byte_values: bytearray):
        """Distance is a two-byte value represented in meters.

        Conversion:
          * Convert the bytes to a little-endian integer
          * Divide by 1000 to get kilometers
          * Multiply by 0.621 to convert kilometers to miles
          * Round to three decimals
        """
        return round(
            (_to_int(byte_values[self._slices["DISTANCE"]]) / 1000.0) * 0.621, 3
        )

    def _extract_timer(self, byte_values: bytearray):
        """Timer is a two-byte value represented in seconds.

        Conversion:
          * Convert the bytes to a little-endian integer (that was simple)

        Note that for the purpose of this the value is kept in seconds - more
        useful calculations (e.g. displaying in a human-readable format) can be
        done by clients.
        """
        return _to_int(byte_values[self._slices["TIMER"]])


class UnknownResponse:
    """Default handler for something we don't yet understand."""

    def __init__(self, raw_bytes: bytearray = None):
        self.raw_bytes = raw_bytes
        self.type = ResponseTypes.UNKNOWN

    def debug_string(self):
        # return f'(UnknownResponse)  {self.raw_bytes.hex()}'
        return f"{self.raw_bytes.hex()}"


def parse_response(response_data: bytearray):
    """Parses raw response data into a structured response.

    The response data always contains the device (M)etadata, followed by a
    two-byte(?) (T)ype. For example:

    010402 2e04 2e0202a0002c01710014000000
    MMMMMM TTTT -------------------------

    Unclear if (T)ype is one or two (or three??) bytes, may need to tweak.

    Note: this assumes the packet headers (packet num/size) have been pruned.
    """
    # Device info most likely allows mapping to different functionality based on
    # the device type (treadmill, bike, unicycle). Ignore for now.
    device_info = response_data[:3]
    response_type = int.from_bytes(response_data[3:7], byteorder="little")

    # Keep the raw byte stuff simple/local rather than make a module-level dict.
    if response_type == 0x22E042E:
        handler = TreadmillStateResponse
    else:
        handler = UnknownResponse

    return handler(response_data[7:])
