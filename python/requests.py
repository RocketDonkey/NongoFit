"""NongoFit - request helpers.

Utilities for building structured requests out of raw data. Once a
PacketReader has assembled a full sequence, the tools here can build a
structured representation of the data.

Known request types:
  * TreadmillStateRequest: request for the current treadmill state
"""

import math

# Maximum size of a single data packet.
_MAX_PACKET_SIZE = 0x12

# Type representing a collection of ordered data packets.
PacketData = list[bytearray]


def to_request_packets(data: bytearray) -> PacketData:
    """Converts `data` into a sequence of bytes that can be sent to a device."""
    if not data:
        raise ValueError("Cannot send empty data, what are your intentions??")

    # The initial packet contains a (C)onstant marker, the (S)ize of the data
    # and the (N)umber of packets, e.g.:
    #
    #   fe02 14 03
    #   CCCC SS NN
    #
    # All values are based on `data` / where it can fit.
    data_size = len(data)
    assert data_size, "No data to send!"

    # Number of packets required to hold the data.
    num_packets = math.ceil(data_size / _MAX_PACKET_SIZE)

    packets = [
        # Header packet (add 1 to account for the header itself).
        bytearray([0xFE, 0x2, data_size, num_packets + 1]),
    ]

    for packet_index in range(num_packets):
        start_index = packet_index * _MAX_PACKET_SIZE
        end_index = start_index + _MAX_PACKET_SIZE
        packet_data = data[start_index:end_index]

        if packet_index + 1 == num_packets:
            # Final packet - store the remaining data and pad if needed.
            packet = bytearray([0xFF, len(packet_data)])
            packet.extend(packet_data)

            padding = _MAX_PACKET_SIZE - len(packet_data)
            packet.extend([0x0] * padding)
            packets.append(packet)
        else:
            # Intermediate packet. First byte is the ordinal packet number,
            # followed by the size)
            packet = bytearray([packet_index, len(packet_data)])
            packet.extend(packet_data)
            packets.append(packet)

    return packets


class TreadmillStateRequest:
    """Request for the current state of the treadmill."""

    # Bytes to request treadmill state.
    #
    # Although this could be hard-coded as a bytearray with control data/etc.,
    # storing it as a string makes it a little easier to see the actual data
    # (even though we have no idea what it means).
    _RAW_BYTES = bytearray.fromhex("02040210041002000a1b94300000405000801827")

    def to_packets(self) -> PacketData:
        return to_request_packets(self._RAW_BYTES)
