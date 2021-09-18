"""NongoFit - packet producers.

Producers output a stream of raw packet bytes, one packet at a time.
"""
import collections
import concurrent.futures
import pygatt
import requests
import time


class FilePacketProducer:
    """Producer that yields packets from a file.

    Each line in the file should represent a single packet in hex format, e.g.:

        fe023204002c4600000000000000000000010000
        00120104022e042e020200000000000000000000
        01120000000001000000000000000000002c0100
        ff0e000000b400000000000000000018002c0100
        ...

    Args:
      filename: path to the file containing the packets.
    """

    def __init__(self, filename: bytes):
        self._filename = filename
        self._file = None

    def __enter__(self):
        self._file = open(self._filename, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()

    def packets(self) -> bytearray:
        """Yields the packets from `_file` as bytearrays."""
        for line in self._file:
            yield bytearray.fromhex(line.strip())


class BluetoothPacketProducer:
    """Producer that yields packets from a BLE stream.

    To start reading from the stream, use it as a context manager, e.g.:

      # This does not immediately start the conneciton.
      ble_producer = BluetoothPacketProducer('<device MAC>')

      with ble_producer as producer:
        # Connection started / closed on exit.
        packet_reader = PacketReader(producer)

    Or if a handle to the producer isn't needed:

      with  BluetoothPacketProducer('<device MAC>') as producer:
        # Connection started / closed on exit.
        packet_reader = PacketReader(producer)
    """

    # The characteristic UUID to which to subscribe to receive value updates.
    # Handle: 0x000b
    _VALUE_UPDATE_UUID = "00001535-1412-efde-1523-785feabcd123"

    # The handle to which to write value request packets.
    _VALUE_REQUEST_HANDLE = 0x000E

    def __init__(self, treadmill_mac: bytes):
        self._treadmill_mac = treadmill_mac

        # Add packets to a FIFO queue so they are yielded in the order received.
        self._buffer = collections.deque()

        # BLE adapter.
        self._adapter = pygatt.GATTToolBackend()

        # The main worker thread is started asynchronously so the loop doesn't
        # block the caller.
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._cancelled = False

        # Device is set upon initialization.
        self._device = None

    def __enter__(self):
        """Initialize the connection with the treadmill and start monitoring."""
        self._adapter.start()
        self._device = self._adapter.connect(
            self._treadmill_mac,
            # Note that this uses random addressing so that the connection can
            # be made to the device regardless of its Bluetooth address.
            address_type=pygatt.BLEAddressType.random,
        )

        # Subscribe to value-change notifications.
        self._device.subscribe(
            self._VALUE_UPDATE_UUID,
            callback=self._handle_value_change,
            wait_for_response=False,
        )

        # Start the loop asynchronouslY.
        self._executor.submit(self._request_update)
        return self

    def _request_update(self):
        req_packets = requests.TreadmillStateRequest().to_packets()
        while not self._cancelled:
            for packet in req_packets:
                self._device.char_write_handle(self._VALUE_REQUEST_HANDLE, packet)
            time.sleep(1)

    def _handle_value_change(self, handle, value):
        """Handles a notification containing the treadmill's current state.

        `value` is a bytearray representing a stream of hex bytes like:

          fe0232040205040502020d0000302a0000000000

        Responses are sent as four separate packets, e.g.:

          fe0232040205040502020d0000302a0000000000
          00120104022e042e0202c1002c0171006a170000
          011200000000025502250b00009112a203b4005d
          ff0e0128015802ec022000ec0220009803b4005d

        This handler buffers all packets and processes them once the final one
        has been received.
        """
        self._buffer.appendleft(value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up state on exit."""
        # Ensure the adapter is stopped.
        self._adapter.stop()
        self._cancelled = True

        self._executor.shutdown()

        # For now this program is stopped by Ctrl+C'ing it, so consider that a
        # normal exit.
        if exc_type == KeyboardInterrupt:
            print("Received stop command - workout complete!")
            return True

    def packets(self):
        while True:
            if not self._buffer:
                time.sleep(0.01)
                continue

            while self._buffer:
                yield self._buffer.pop()
