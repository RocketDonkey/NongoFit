import requests
import unittest


class RequestsTest(unittest.TestCase):
    def test_empty_data(self):
        with self.assertRaises(ValueError):
            requests.to_request_packets(bytearray([]))

    def test_two_packet_request(self):
        # Final packet has a single 0x1.
        data = bytearray([0x1])
        req_bytes = requests.to_request_packets(data)

        # Convert to hex for easier verification.
        hexxed = [raw.hex() for raw in req_bytes]

        self.assertEqual(
            hexxed, ["fe020102", "ff01010000000000000000000000000000000000"]
        )

    def test_three_packet_request(self):
        # Middle packet has all 0x1's, final packet has a single 0x2.
        data = bytearray([])
        data.extend([0x1] * 0x12)
        data.append(0x2)

        req_bytes = requests.to_request_packets(data)

        # Convert to hex for easier verification.
        hexxed = [raw.hex() for raw in req_bytes]

        self.assertEqual(
            hexxed,
            [
                "fe021303",
                "0012010101010101010101010101010101010101",
                "ff01020000000000000000000000000000000000",
            ],
        )

    def test_four_packet_request(self):
        # First middle packet has all 0x1's, second has all 0x2's,  final
        # packet has all 0x3's.
        data = bytearray([])
        data.extend([0x1] * 0x12)
        data.extend([0x2] * 0x12)
        data.extend([0x3] * 0x12)

        req_bytes = requests.to_request_packets(data)

        # Convert to hex for easier verification.
        hexxed = [raw.hex() for raw in req_bytes]

        self.assertEqual(
            hexxed,
            [
                "fe023604",
                "0012010101010101010101010101010101010101",
                "0112020202020202020202020202020202020202",
                "ff12030303030303030303030303030303030303",
            ],
        )

    def test_treadmill_state_request(self):
        hexxed = [raw.hex() for raw in requests.TreadmillStateRequest().to_packets()]

        self.assertEqual(
            hexxed,
            [
                "fe021403",
                "001202040210041002000a1b9430000040500080",
                "ff02182700000000000000000000000000000000",
            ],
        )


if __name__ == "__main__":
    unittest.main()
