"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

from opendbc.car import uds
from opendbc.car.carlog import carlog
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery

DEVELOPER_DIAGNOSTIC = 0x07
CUSTOM_DIAGNOSTIC_REQUEST = bytes([uds.SERVICE_TYPE.DIAGNOSTIC_SESSION_CONTROL, DEVELOPER_DIAGNOSTIC])
CUSTOM_DIAGNOSTIC_RESPONSE = bytes([uds.SERVICE_TYPE.DIAGNOSTIC_SESSION_CONTROL + 0x40, DEVELOPER_DIAGNOSTIC])
EXT_DIAG_REQUEST = b'\x10\x03'
EXT_DIAG_RESPONSE = b'\x50\x03'

READ_DATA_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER])
READ_DATA_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40])

WRITE_DATA_REQUEST = bytes([uds.SERVICE_TYPE.WRITE_DATA_BY_IDENTIFIER])
WRITE_DATA_RESPONSE = bytes([uds.SERVICE_TYPE.WRITE_DATA_BY_IDENTIFIER + 0x40])

CONFIG_DATA_ID = bytes([0x01, 0x42])
DEFAULT_CONFIG = bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x00])
TRACKS_ENABLED_CONFIG = bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x01])
TRACKS_ENABLED_CONFIG_BYTES = b"\x00\x00\x01\x00\x01"

RESET_REQUEST = b'\x11\x01'
RESET_RESPONSE = b''


def enable_radar_tracks(logcan, sendcan, bus=0, addr=0x7d0, timeout=0.1, retry=2, reset=True):
  carlog.error("radar_tracks: enabling ...")

  if reset:
    try:
      # Send reset first because the disable request below is not getting to the radar soon enough
      carlog.error("sending reset (0x11 0x01) ...")
      reset_query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [RESET_REQUEST], [RESET_RESPONSE])
      reset_query.get_data(timeout=0.1)
    except Exception:
      carlog.error("reset failed or unsupported")

  for i in range(retry):
    try:
      query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [EXT_DIAG_REQUEST], [EXT_DIAG_RESPONSE])

      for (rx_addr, _), data in query.get_data(timeout).items():
        carlog.error(f"Received response from 0x{rx_addr:X} on bus {bus}: {data.hex()}")
        carlog.error("radar_tracks: check current config ...")

        request = READ_DATA_REQUEST + CONFIG_DATA_ID
        query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [request], [READ_DATA_RESPONSE])

        for (rx_addr, _), data in query.get_data(timeout).items():
          carlog.error(f"Received response from 0x{rx_addr:X} on bus {bus}: {data.hex()}")
          current_config = data[3:]

          carlog.error(f"radar_tracks: current config: {current_config.hex()}")

          if current_config == TRACKS_ENABLED_CONFIG_BYTES:
            carlog.error("radar_tracks: already enabled, skipping ...")
          else:
            carlog.error("radar_tracks: reconfigure radar to output radar points ...")
            request = WRITE_DATA_REQUEST + CONFIG_DATA_ID + TRACKS_ENABLED_CONFIG
            query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [request], [WRITE_DATA_RESPONSE])
            query.get_data(0)

            carlog.error("radar_tracks: successfully enabled")

          return True

    except Exception as e:
      carlog.exception(f"radar_tracks exception: {e}")

    carlog.error(f"radar_tracks retry ({i + 1}) ...")
  carlog.error("radar_tracks: failed")
  return False


if __name__ == "__main__":
  import time
  import cereal.messaging as messaging

  sendcan_sock = messaging.pub_sock('sendcan')
  logcan_sock = messaging.sub_sock('can')

  def sendcan(msgs):
    m = messaging.new_message('sendcan', len(msgs))
    for i, msg in enumerate(msgs):
      m.sendcan[i].address = msg.address
      m.sendcan[i].dat = msg.dat
      m.sendcan[i].src = msg.src
    sendcan_sock.send(m.to_bytes())

  def logcan(*args, **kwargs):
    msg = messaging.recv_sock(logcan_sock)
    if msg is None:
      return []
    return msg.can

  time.sleep(1)

  enabled = enable_radar_tracks(logcan, sendcan, bus=0, addr=0x7d0, timeout=0.1)
  print(f"enabled: {enabled}")
