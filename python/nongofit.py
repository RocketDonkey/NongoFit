#!/usr/bin/python3
"""NongoFit runner.

This reads a stream of Bluetooth packets from a NordticTrack 6.5T treadmill (and
maybe other devices with iFit) and writes responses in a structured format.

Usage:
    ./nongofit.py --treadmill_address=<MAC> --output_directory=/some/path

That will connect to the treadmill at <MAC> and start writing state to
--output_directory.
"""

import argparse
import contextlib
import csv
import datetime
import os
import packet_reader
import producers
import responses


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Process the Bluetooth LE output of a NordicTrack T "
            "Series 6.5S treadmill"
        )
    )

    # Input options - only one allowed.
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--treadmill_address",
        type=str,
        required=False,
        help="MAC address of the treadmill to which to connect",
    )
    input_group.add_argument(
        "--input_file",
        type=str,
        required=False,
        help="Path to a file containing raw packet data; mostly useful "
        "for debugging",
    )

    # Output options.
    parser.add_argument(
        "--output_directory",
        type=str,
        required=False,
        help=(
            "Directory to which to write output data; the file will be "
            "named YYYYmmdd_HHMMSS.csv; if unset, write nothing"
        ),
    )
    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        help=("Whether to write debug output to stdout"),
    )
    args = parser.parse_args()

    if args.treadmill_address:
        producer = producers.BluetoothPacketProducer(args.treadmill_address)
    else:
        producer = producers.FilePacketProducer(args.input_file)

    if args.output_directory:
        output_path = os.path.join(
            args.output_directory, f"{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        output_file = open(output_path, "w")
        csv_writer = csv.DictWriter(
            output_file, fieldnames=("incline", "pace", "distance", "timer")
        )
        csv_writer.writeheader()
    else:
        output_file = contextlib.nullcontext()
        csv_writer = None

    with contextlib.ExitStack() as stack:
        producer = stack.enter_context(producer)
        output = stack.enter_context(output_file)

        reader = packet_reader.PacketReader(producer)
        for response_data in reader.responses():
            if not (response := responses.parse_response(response_data)):
                continue

            if response.type == responses.ResponseTypes.TREADMILL_STATE:
                if args.debug:
                    print(response.debug_string())
                if csv_writer is not None:
                    csv_writer.writerow(response.to_dict())


if __name__ == "__main__":
    main()
