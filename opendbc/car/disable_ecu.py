import time
from opendbc.car.carlog import carlog
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery

EXT_DIAG_REQUEST = b'\x10\x03'
EXT_DIAG_RESPONSE = b'\x50\x03'

RESET_REQUEST = b'\x11\x01'
RESET_RESPONSE = b''
CONFIRM_TIMEOUT = 1.0

COM_CONT_RESPONSE = b''


def disable_ecu(can_recv, can_send, bus=0, addr=0x7d0, sub_addr=None, com_cont_req=b'\x28\x83\x01', timeout=0.1, retry=10, reset=False):
  """Silence an ECU by disabling sending and receiving messages using UDS 0x28.
  The ECU will stay silent as long as openpilot keeps sending Tester Present.

  This is used to disable the radar in some cars. Openpilot will emulate the radar.
  WARNING: THIS DISABLES AEB!"""

  def confirm_radar_silent(msg):
    if msg[0] == 0x7F:
      carlog.error(f"Negative response from ECU: {msg.hex()}")
      return False
    else:
      return True

  carlog.warning(f"ecu disable {hex(addr), sub_addr} ...")

  if reset:
    try:
      # Send reset first because the disable request below is not getting to the radar soon enough
      carlog.error("sending reset (0x11 0x01) ...")
      reset_query = IsoTpParallelQuery(can_send, can_recv, bus, [(addr, sub_addr)], [RESET_REQUEST], [RESET_RESPONSE])
      reset_query.get_data(timeout=0.1)
    except Exception:
      carlog.error("reset failed or unsupported")

  for i in range(retry):
    try:
      query = IsoTpParallelQuery(can_send, can_recv, bus, [(addr, sub_addr)], [EXT_DIAG_REQUEST], [EXT_DIAG_RESPONSE])

      results = query.get_data(timeout)
      for (rx_addr, _), data in results.items():
        carlog.error(f"Received EXT_DIAG_RESPONSE from 0x{rx_addr:X} on bus {bus}: {data.hex()}")

        query = IsoTpParallelQuery(can_send, can_recv, bus, [(addr, sub_addr)], [com_cont_req], [COM_CONT_RESPONSE])
        results = query.get_data(0)
        for (rx_addr, _), data in results.items():
          carlog.error(f"Received COM_CONT_RESPONSE from 0x{rx_addr:X} on bus {bus}: {data.hex()}")

        # Confirm radar silence after disable
        if confirm_radar_silent(data):
          carlog.error(f"ecu disabled on bus {bus}")
          return True
        else:
          carlog.error("Radar still transmitting after disable attempt")

    except Exception:
      carlog.exception("ecu disable exception")

    carlog.error(f"ecu disable retry ({i + 1}) ...bus {bus}")
  carlog.error(f"ecu disable failed bus {bus}")
  return False