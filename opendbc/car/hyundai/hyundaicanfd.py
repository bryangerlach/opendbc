import copy
import numpy as np
from opendbc.car import CanBusBase
from opendbc.car.hyundai.values import HyundaiFlags
from opendbc.car.hyundai.hyundaican import hyundai_checksum


class CanBus(CanBusBase):
  def __init__(self, CP, fingerprint=None, lka_steering=None) -> None:
    super().__init__(CP, fingerprint)

    if lka_steering is None:
      lka_steering = CP.flags & HyundaiFlags.CANFD_LKA_STEERING.value if CP is not None else False

    # On the CAN-FD platforms, the LKAS camera is on both A-CAN and E-CAN. LKA steering cars
    # have a different harness than the LFA steering variants in order to split
    # a different bus, since the steering is done by different ECUs.
    self._a, self._e = 1, 0
    if lka_steering:
      self._a, self._e = 0, 1

    self._a += self.offset
    self._e += self.offset
    self._cam = 2 + self.offset

  @property
  def ECAN(self):
    return self._e

  @property
  def ACAN(self):
    return self._a

  @property
  def CAM(self):
    return self._cam


def create_steering_messages(packer, CP, CAN, enabled, lat_active, apply_torque,
                            frame, torque_fault, left_lane, right_lane,
                            left_lane_depart, right_lane_depart, lkas_icon):
  common_values = {
    "LKA_MODE": 2,
    "LKA_ICON": lkas_icon,
    "TORQUE_REQUEST": apply_torque,
    "LKA_ASSIST": 0,
    "STEER_REQ": 1 if lat_active else 0,
    "STEER_MODE": 0,
    "HAS_LANE_SAFETY": 0,  # hide LKAS settings
    "NEW_SIGNAL_2": 0,
  }

  lkas_values = copy.copy(common_values)
  lkas_values["LKA_AVAILABLE"] = 0

  lfa_values = copy.copy(common_values)
  lfa_values["NEW_SIGNAL_1"] = 0

  ret = []
  if CP.flags & HyundaiFlags.CANFD_LKA_STEERING:
    lkas_msg = "LKAS_ALT" if CP.flags & HyundaiFlags.CANFD_LKA_STEERING_ALT else "LKAS"
    if CP.openpilotLongitudinalControl:
      if CP.flags & HyundaiFlags.CAN_CANFD_BLENDED:
        ret.append(create_lkas11_can_canfd_blended(packer, CAN, frame, apply_torque, lat_active,
                                                  torque_fault, enabled,
                                                  left_lane, right_lane,
                                                  left_lane_depart, right_lane_depart))
      else:
        ret.append(packer.make_can_msg("LFA", CAN.ECAN, lfa_values))
    ret.append(packer.make_can_msg(lkas_msg, CAN.ACAN, lkas_values))
  else:
    ret.append(packer.make_can_msg("LFA", CAN.ECAN, lfa_values))

  return ret

def create_suppress_lfa(packer, CAN, lfa_block_msg, lka_steering_alt):
  suppress_msg = "CAM_0x362" if lka_steering_alt else "CAM_0x2a4"
  msg_bytes = 32 if lka_steering_alt else 24

  values = {f"BYTE{i}": lfa_block_msg[f"BYTE{i}"] for i in range(3, msg_bytes) if i != 7}
  values["COUNTER"] = lfa_block_msg["COUNTER"]
  values["SET_ME_0"] = 0
  values["SET_ME_0_2"] = 0
  values["LEFT_LANE_LINE"] = 0
  values["RIGHT_LANE_LINE"] = 0
  return packer.make_can_msg(suppress_msg, CAN.ACAN, values)

def create_lkas11_can_canfd_blended(packer, CAN, frame, apply_steer, steer_req,
                                   torque_fault, enabled,
                                   left_lane, right_lane,
                                   left_lane_depart, right_lane_depart):

  values = {
    "CF_Lkas_LdwsLHWarning": left_lane_depart,
    "CF_Lkas_LdwsRHWarning": right_lane_depart,
    "CR_Lkas_StrToqReq": apply_steer,
    "CF_Lkas_ActToi": steer_req,
    "CF_Lkas_ToiFlt": torque_fault,  # seems to allow actuation on CR_Lkas_StrToqReq
    "CF_Lkas_MsgCount": frame % 0xF,
    "CF_Lkas_FcwOpt_USM": 2 if enabled else 1,
    "CF_Lkas_LdwsActivemode": int(left_lane) + (int(right_lane) << 1),
    "NEW_SIGNAL_1": 0,
    "NEW_SIGNAL_5": 100,
  }

  checksum = create_checksum_can_canfd_blended(packer, CAN, "LKAS11", values)
  values["CF_Lkas_Chksum"] = checksum

  return packer.make_can_msg("LKAS11", CAN.ECAN, values)

def create_buttons(packer, CP, CAN, cnt, btn):
  values = {
    "COUNTER": cnt,
    "SET_ME_1": 1,
    "CRUISE_BUTTONS": btn,
  }

  bus = CAN.ECAN if CP.flags & HyundaiFlags.CANFD_LKA_STEERING else CAN.CAM
  return packer.make_can_msg("CRUISE_BUTTONS", bus, values)

def create_acc_cancel(packer, CP, CAN, cruise_info_copy):
  # TODO: why do we copy different values here?
  if CP.flags & HyundaiFlags.CANFD_CAMERA_SCC.value:
    values = {s: cruise_info_copy[s] for s in [
      "COUNTER",
      "CHECKSUM",
      "NEW_SIGNAL_1",
      "MainMode_ACC",
      "ACCMode",
      "ZEROS_9",
      "CRUISE_STANDSTILL",
      "ZEROS_5",
      "DISTANCE_SETTING",
      "VSetDis",
    ]}
  else:
    values = {s: cruise_info_copy[s] for s in [
      "COUNTER",
      "CHECKSUM",
      "ACCMode",
      "VSetDis",
      "CRUISE_STANDSTILL",
    ]}
  values.update({
    "ACCMode": 4,
    "aReqRaw": 0.0,
    "aReqValue": 0.0,
  })
  return packer.make_can_msg("SCC_CONTROL", CAN.ECAN, values)

def create_lfahda_cluster(packer, CAN, enabled, lfa_icon, can_canfd_blended):
  hda_icon = "HDA_Icon_State" if can_canfd_blended else "HDA_ICON"
  lfa_icon = "LFA_Icon_State" if can_canfd_blended else "LFA_ICON"

  values = {
    hda_icon: 1 if enabled and not can_canfd_blended else 0,
    lfa_icon: 2 if enabled else 0,
  }

  msg = "LFAHDA_MFC" if can_canfd_blended else "LFAHDA_CLUSTER"
  if can_canfd_blended:
    checksum = create_checksum_can_canfd_blended(packer, CAN, msg, values)
    values["CHECKSUM"] = checksum

  return packer.make_can_msg(msg, CAN.ECAN, values)


def create_acc_control(packer, CAN, enabled, accel_last, accel, stopping, gas_override, set_speed, hud_control,
                       main_cruise_enabled, tuning):
  jerk = 5
  jn = jerk / 50
  if not enabled or gas_override:
    a_val, a_raw = 0, 0
  else:
    a_raw = accel  # noqa: F841
    a_val = np.clip(accel, accel_last - jn, accel_last + jn)  # noqa: F841

  values = {
    "ACCMode": 0 if not enabled else (2 if gas_override else 1),
    "MainMode_ACC": 1 if main_cruise_enabled else 0,
    "StopReq": 1 if tuning.stopping else 0,
    "aReqValue": tuning.actual_accel,
    "aReqRaw": tuning.actual_accel,
    "VSetDis": set_speed,
    "JerkLowerLimit": tuning.jerk_lower,
    "JerkUpperLimit": tuning.jerk_upper,

    "ACC_ObjDist": 1,
    "ObjValid": 0,
    "OBJ_STATUS": 2,
    "SET_ME_2": 0x4,
    "SET_ME_3": 0x3,
    "SET_ME_TMP_64": 0x64,
    "DISTANCE_SETTING": hud_control.leadDistanceBars,
  }

  return packer.make_can_msg("SCC_CONTROL", CAN.ECAN, values)

def create_acc_commands_can_canfd_blended(packer, CAN, enabled, accel, accel_last, upper_jerk, idx, lead_visible, set_speed, stopping, long_override, hud_control):
  jerk = 5
  jn = jerk / 50
  if not enabled or long_override:
    a_val, a_raw = 0, 0
  else:
    a_raw = accel
    a_val = np.clip(accel, accel_last - jn, accel_last + jn)
  ret = []

  msg_values = [
    ("SCC11", {
      "aReqRaw": a_raw,
      "aReqValue": a_val,
      "JerkUpperLimit": upper_jerk,
      "JerkLowerLimit": jerk if enabled else 1,
    }),

    ("SCC12", {
      "MainMode_ACC": 1,
      "ACCMode_Inactive": 0 if enabled else 1,
      "TauGapSet": hud_control.leadDistanceBars,
      "VSetDis": set_speed,
      "ACC_ObjDist": 1,
      "ACCMode": 2 if enabled and long_override else 1 if enabled else 0,
      "StopReq": 1 if stopping else 0,
    }),

    ("SCC14", {
      "ACC_ObjLatPos": 0,
      "ObjValid": 0,
      "ObjStatus": 0 if not lead_visible else 2 if lead_visible and enabled else 1,
    }),

    ("FCA11", {
      "BYTE4": 0xC0,
      "BYTE5": 0x3F,
      "BYTE6": 0x7F,
    }),
  ]

  for addr, values in msg_values:
    values["COUNTER"] = idx % 0xF
    checksum = create_checksum_can_canfd_blended(packer, CAN, addr, values)
    values["CHECKSUM"] = checksum
    ret.append(packer.make_can_msg(addr, CAN.ECAN, values))

  return ret

def create_spas_messages(packer, CAN, left_blink, right_blink):
  ret = []

  values = {
  }
  ret.append(packer.make_can_msg("SPAS1", CAN.ECAN, values))

  blink = 0
  if left_blink:
    blink = 3
  elif right_blink:
    blink = 4
  values = {
    "BLINKER_CONTROL": blink,
  }
  ret.append(packer.make_can_msg("SPAS2", CAN.ECAN, values))

  return ret


def create_fca_warning_light(packer, CAN, frame):
  ret = []

  if frame % 2 == 0:
    values = {
      'AEB_SETTING': 0x1,  # show AEB disabled icon
      'SET_ME_2': 0x2,
      'SET_ME_FF': 0xff,
      'SET_ME_FC': 0xfc,
      'SET_ME_9': 0x9,
    }
    ret.append(packer.make_can_msg("ADRV_0x160", CAN.ECAN, values))
  return ret


def create_adrv_messages(packer, CAN, frame, can_canfd_blended):
  # messages needed to car happy after disabling
  # the ADAS Driving ECU to do longitudinal control

  ret = []

  values = {
  }
  ret.append(packer.make_can_msg("ADRV_0x51", CAN.ACAN, values))

  #ret.extend(create_fca_warning_light(packer, CAN, frame))

  if not can_canfd_blended:
    if frame % 5 == 0:
      values = {
        'SET_ME_1C': 0x1c,
        'SET_ME_FF': 0xff,
        'SET_ME_TMP_F': 0xf,
        'SET_ME_TMP_F_2': 0xf,
      }
      ret.append(packer.make_can_msg("ADRV_0x1ea", CAN.ECAN, values))

      values = {
        'SET_ME_E1': 0xe1,
        'SET_ME_3A': 0x3a,
      }
      ret.append(packer.make_can_msg("ADRV_0x200", CAN.ECAN, values))

    if frame % 20 == 0:
      values = {
        'SET_ME_15': 0x15,
      }
      ret.append(packer.make_can_msg("ADRV_0x345", CAN.ECAN, values))

    if frame % 100 == 0:
      values = {
        'SET_ME_22': 0x22,
        'SET_ME_41': 0x41,
      }
      ret.append(packer.make_can_msg("ADRV_0x1da", CAN.ECAN, values))

  return ret

def create_radar_aux_messages(packer, CAN, frame):
  ret = []

  msg_values = [
    ("RADAR_0x363", 2,  {
      "FCA_ESA": 1,
    }),
    ("RADAR_0x398", 5,  {
      "BYTE4": 0x80,
      "BYTE5": 0x5D,
    }),
    ("RADAR_0x399", 5,  {
      "BYTE2": 0x02,
    }),
    ("RADAR_0x39a", 5,  {
      "BYTE7": 0xFF,
    }),
    ("RADAR_0x39b", 5,  {
    }),
    ("RADAR_0x39c", 5,  {
      "BYTE5": 0xE0,
      "BYTE6": 0x79,
    }),
    ("RADAR_0x43a", 20, {
      "BYTE2": 0x07,
    }),
  ]

  for addr, freq, values in msg_values:
    if frame % freq == 0:
      values["COUNTER"] = frame % 0xF
      checksum = create_checksum_can_canfd_blended(packer, CAN, addr, values)
      values["CHECKSUM"] = checksum
      ret.append(packer.make_can_msg(addr, CAN.ECAN, values))

  return ret

def create_checksum_can_canfd_blended(packer, CAN, addr, values):
  dat = packer.make_can_msg(addr, CAN.ECAN, values)[1]
  dat = dat[1:8]
  checksum = hyundai_checksum(dat)

  return checksum
