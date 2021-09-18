"""NongoFit - packet readers.

Packet readers read packets from a producer and generate meaning responses.

Example usage:

    # Create a file-based packet producer and print out each collected response.
    with FilePacketProducer('packets.txt') as packet_producer:
        reader = packet_reader.PacketReader(packet_producer)
        for response_data in reader.responses():
            if (response := responses.parse_response(response_data)):
                print(response.debug_string())

See additional documentation below.
"""


class PacketReader:
    """Reads packets from a producer and combines them into meaningful data.

    This is the low-level packet aggregator - it has no knowledge of the
    underlying data and is only responsible for assembling the packets into a
    single bundle of data.

    For example, given a producer that yields the following packets:

        fe02320402060406900208a46e0e005702b4002b
        00120104022e042e0202a0002c0171005b0c0000
        011200000001023203421700007a641f02b4002b
        ff0e01790058028a760e008a760e003a02b4002b

    The PacketReader verifies/strips markers/packet lengths/etc. and outputs a
    single stream of data bytes, e.g.:

        0104022e042e0202a0002c0171005b0c000000000001023....
    """

    # Bytes marking the first/last packets in a sequences.
    HEADER_MARKER = b"\xfe\x02"
    END_MARKER = b"\xff"

    def __init__(self, producer):
        """Builds a PacketReader.

        Args:
            `producer`: yields packets for processig.
        """
        self._producer = producer
        self._reset()

        # The sequence_num carries over between sequences so it is not reset.
        self._sequence_num = None

    def _reset(self):
        """Resets the state and prepares for the next sequence."""
        self._packets_remaining = 0
        self._last_packet_index = -1

        self._current_data = bytearray()

    def responses(self):
        """Generator that returns fully assembled responses."""
        for packet in self._producer.packets():
            if packet.startswith(self.HEADER_MARKER):
                self._handle_header_packet(packet)
            elif packet.startswith(self.END_MARKER):
                # Last packet -> prepare for response!
                self._handle_end_packet(packet)
                yield self._current_data

                # Prep for the next sequence.
                self._reset()
            else:
                self._handle_intermediate_packet(packet)

    def _handle_header_packet(self, packet: bytearray):
        """Parses the first packet in a sequence.

        The initial packet contains the (H)eader, (C)hecksum based on the size,
        (P)acket count and (D)ata.

        Example:
          fe02 32 04 02060406900208a46e0e005702b4002b
          HHHH CC PP DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
        """
        num_packets = packet[3]
        sequence_num = packet[4:]

        self._packets_remaining = num_packets - 1

        # Note: no data is extracted from the this packet - it is pure metadata.

        if self._sequence_num is not None:
            assert self._sequence_num == sequence_num, (
                f"Sequence number mismatch: expected "
                f"{self._sequence_num.hex()}, got {sequence_num.hex()}"
            )

    def _handle_intermediate_packet(self, packet: bytearray):
        """Parses an intermediate (between the first and last) packet.

        These contain the (N)umber of the packet, (S)ize of the data in this
        packet and (D)ata.

        Example:
          00 12 0104022e042e0202a0002c0171005b0c0000
          NN SS DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
        """
        # Extract the (N)umber and (S)ize.
        packet_index = packet[0]
        data_size = packet[1]
        packet = packet[2:]

        # Are we expecting you?
        assert packet_index == self._last_packet_index + 1
        self._last_packet_index = packet_index

        self._current_data.extend(packet)
        self._packets_remaining -= 1

    def _handle_end_packet(self, packet: bytearray):
        """Parses the last packet in a sequence.

        The final packet contains the (H)eader, (S)ize and (D)ata.

        Note that the final 16 bytes of (D)ata double as the (S)equence number
        used by the next sequence.

        Example:
          ff 0e 01790058028a760e008a760e003a02b4002b
          HH CC DDDDDDDDDDDDDDDDDDDDDDDDDDDD
                    SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS
        """
        data_size = packet[1]
        data = packet[2 : data_size + 1]
        sequence_num = packet[4:]
        self._sequence_num = sequence_num
        self._current_data.extend(data)

        # Ensure no tomfoolerly happened.
        assert (
            self._packets_remaining == 1
        ), f"Unexpected number of packets: {self._packets_remaining}"
