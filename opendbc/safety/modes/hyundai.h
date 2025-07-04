#pragma once

#include "opendbc/safety/safety_declarations.h"
#include "opendbc/safety/modes/hyundai_common.h"

#define HYUNDAI_LIMITS(steer, rate_up, rate_down, drv_trq_allowance) { \
  .max_torque = (steer), \
  .max_rate_up = (rate_up), \
  .max_rate_down = (rate_down), \
  .max_rt_delta = 112, \
  .driver_torque_allowance = drv_trq_allowance, \
  .driver_torque_multiplier = 2, \
  .type = TorqueDriverLimited, \
   /* the EPS faults when the steering angle is above a certain threshold for too long. to prevent this, */ \
   /* we allow setting CF_Lkas_ActToi bit to 0 while maintaining the requested torque value for two consecutive frames */ \
  .min_valid_request_frames = 89, \
  .max_invalid_request_frames = 2, \
  .min_valid_request_rt_interval = 810000,  /* 810ms; a ~10% buffer on cutting every 90 frames */ \
  .has_steer_req_tolerance = true, \
}

extern const LongitudinalLimits HYUNDAI_LONG_LIMITS;
const LongitudinalLimits HYUNDAI_LONG_LIMITS = {
  .max_accel = 200,   // 1/100 m/s2
  .min_accel = -350,  // 1/100 m/s2
};

#define HYUNDAI_COMMON_TX_MSGS(scc_bus) \
  {0x340, 0,       8, .check_relay = true},   /* LKAS11 Bus 0                              */ \
  {0x4F1, scc_bus, 4, .check_relay = false},  /* CLU11 Bus 0 (radar-SCC) or 2 (camera-SCC) */ \
  {0x485, 0,       4, .check_relay = true},   /* LFAHDA_MFC Bus 0                          */ \

static const CanMsg HYUNDAI_CAN_CANFD_BLENDED_HDA2_TX_MSGS[] = {
  {0x50, 0, 16, .check_relay = true},
  {0x4F1, 1, 4, .check_relay = false},
  {0x2A4, 0, 24, .check_relay = true},
};

static const CanMsg HYUNDAI_CAN_CANFD_BLENDED_HDA2_LONG_TX_MSGS[] = {
  {0x50, 0, 16, .check_relay = true},
  {0x4F1, 1, 4, .check_relay = false},
  {0x2A4, 0, 24, .check_relay = true},
  {0x51, 0, 32, .check_relay = false},
  {0x730, 1, 8, .check_relay = false},
  {0x340, 1, 8, .check_relay = true},
  {0x485, 1, 8, .check_relay = true},
  {0x420, 1, 8, .check_relay = true},
  {0x421, 1, 8, .check_relay = true},
  {0x389, 1, 8, .check_relay = true},
  {0x38D, 1, 8, .check_relay = false},
  {0x363, 1, 8, .check_relay = false},
  {0x398, 1, 8, .check_relay = false},
  {0x399, 1, 8, .check_relay = false},
  {0x39a, 1, 8, .check_relay = false},
  {0x39b, 1, 8, .check_relay = false},
  {0x39c, 1, 8, .check_relay = false},
  {0x43a, 1, 8, .check_relay = false},
  {0x7D0, 0, 8, .check_relay = false},
};


#define HYUNDAI_LONG_COMMON_TX_MSGS(scc_bus) \
  HYUNDAI_COMMON_TX_MSGS(scc_bus) \
  {0x420, 0,       8, .check_relay = true},   /* SCC11 Bus 0       */ \
  {0x421, 0,       8, .check_relay = true},   /* SCC12 Bus 0       */ \
  {0x50A, 0,       8, .check_relay = true},   /* SCC13 Bus 0       */ \
  {0x389, 0,       8, .check_relay = true},   /* SCC14 Bus 0       */ \
  {0x4A2, 0,       2, .check_relay = false},  /* FRT_RADAR11 Bus 0 */ \

#define HYUNDAI_COMMON_RX_CHECKS(legacy, can_canfd_blended, pt_bus)                                                                                                                                               \
  {.msg = {{0x260, (pt_bus), 8, .max_counter = 3U, .ignore_quality_flag = true, .frequency = 100U},                                                                                           \
           {0x371, 0, 8, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true, .frequency = 100U}, { 0 }}},                                                    \
  {.msg = {{0x386, (pt_bus), 8, .ignore_checksum = (legacy), .ignore_counter = (legacy), .max_counter = (legacy) ? 0U : 15U, .ignore_quality_flag = true, .frequency = (can_canfd_blended) ? 50U :100U}, { 0 }, { 0 }}}, \
  {.msg = {{0x394, (pt_bus), 8, .ignore_checksum = (legacy), .ignore_counter = (legacy), .max_counter = (legacy) ? 0U : 7U, .ignore_quality_flag = true, .frequency = (can_canfd_blended) ? 50U : 100U}, { 0 }, { 0 }}},                                        \

#define HYUNDAI_SCC11_ADDR_CHECK(scc_bus)                                                                                                         \
  {.msg = {{0x420, (scc_bus), 8, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true, .frequency = 50U}, { 0 }, { 0 }}}, \

#define HYUNDAI_SCC12_ADDR_CHECK(can_canfd_blended, scc_bus)                                                                            \
  {.msg = {{0x421, (scc_bus), 8, .ignore_checksum = (can_canfd_blended), .max_counter = 15U, .frequency = 50U}, { 0 }, { 0 }}}, \

#define HYUNDAI_FCEV_GAS_ADDR_CHECK \
  {.msg = {{0x91,  0, 8, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true, .frequency = 100U}, { 0 }, { 0 }}}, \

#define HYUNDAI_LDA_BUTTON_ADDR_CHECK \
  {.msg = {{0x391, 0, 8, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true, .frequency = 50U}, { 0 }, { 0 }}}, \

static const CanMsg HYUNDAI_TX_MSGS[] = {
  HYUNDAI_COMMON_TX_MSGS(0)
};

RxCheck hyundai_rx_checks[] = {
   HYUNDAI_COMMON_RX_CHECKS(false, false, 0)
   HYUNDAI_SCC12_ADDR_CHECK(false, 0)
};

RxCheck hyundai_can_canfd_blended_hda2_rx_checks[] = {
  HYUNDAI_COMMON_RX_CHECKS(false, true, 1)
  HYUNDAI_SCC12_ADDR_CHECK(true, 1)
};

RxCheck hyundai_can_canfd_blended_hda2_long_rx_checks[] = {
  HYUNDAI_COMMON_RX_CHECKS(false, true, 1)
  {.msg = {{0x4F1, 1, 4, .ignore_checksum = true, .max_counter = 15U, .ignore_quality_flag = true, .frequency = 50U}, { 0 }, { 0 }}},
};

static bool hyundai_legacy = false;

static uint8_t hyundai_get_counter(const CANPacket_t *to_push) {
  int addr = GET_ADDR(to_push);

  uint8_t cnt = 0;
  if (addr == 0x260) {
    cnt = (GET_BYTE(to_push, 7) >> 4) & 0x3U;
  } else if (addr == 0x386) {
    cnt = ((GET_BYTE(to_push, 3) >> 6) << 2) | (GET_BYTE(to_push, 1) >> 6);
  } else if (addr == 0x394) {
    cnt = (GET_BYTE(to_push, 1) >> 5) & 0x7U;
  } else if (addr == 0x421) {
    cnt = (hyundai_can_canfd_blended ? (GET_BYTE(to_push, 1) >> 4) : GET_BYTE(to_push, 7)) & 0xFU;
  } else if (addr == 0x4F1) {
    cnt = (GET_BYTE(to_push, 3) >> 4) & 0xFU;
  } else {
  }
  return cnt;
}

static uint32_t hyundai_get_checksum(const CANPacket_t *to_push) {
  int addr = GET_ADDR(to_push);

  uint8_t chksum = 0;
  if (addr == 0x260) {
    chksum = GET_BYTE(to_push, 7) & 0xFU;
  } else if (addr == 0x386) {
    chksum = ((GET_BYTE(to_push, 7) >> 6) << 2) | (GET_BYTE(to_push, 5) >> 6);
  } else if (addr == 0x394) {
    chksum = GET_BYTE(to_push, 6) & 0xFU;
  } else if (addr == 0x421) {
    chksum = hyundai_can_canfd_blended ? GET_BYTE(to_push, 0) : GET_BYTE(to_push, 7) >> 4;
  } else {
  }
  return chksum;
}

static uint32_t hyundai_compute_checksum(const CANPacket_t *to_push) {
  int addr = GET_ADDR(to_push);

  uint16_t chksum = 0;
  if (addr == 0x386) {
    // count the bits
    for (int i = 0; i < 8; i++) {
      uint8_t b = GET_BYTE(to_push, i);
      for (int j = 0; j < 8; j++) {
        uint8_t bit = 0;
        // exclude checksum and counter
        if (((i != 1) || (j < 6)) && ((i != 3) || (j < 6)) && ((i != 5) || (j < 6)) && ((i != 7) || (j < 6))) {
          bit = (b >> (uint8_t)j) & 1U;
        }
        chksum += bit;
      }
    }
    chksum = (chksum ^ 9U) & 15U;
  } else {
    if (hyundai_can_canfd_blended && (addr == 0x421)) {
      chksum = hyundai_common_canfd_compute_checksum(to_push);
    } else {
      // sum of nibbles
      for (int i = 0; i < 8; i++) {
        if ((addr == 0x394) && (i == 7)) {
          continue; // exclude
        }
        uint8_t b = GET_BYTE(to_push, i);
        if (((addr == 0x260) && (i == 7)) || ((addr == 0x394) && (i == 6)) || ((addr == 0x421) && (i == 7))) {
          b &= (addr == 0x421) ? 0x0FU : 0xF0U; // remove checksum
        }
        chksum += (b % 16U) + (b / 16U);
      }
      chksum = (16U - (chksum %  16U)) % 16U;
    }
  }

  return chksum;
}

static void hyundai_rx_hook(const CANPacket_t *to_push) {
  int bus = GET_BUS(to_push);
  int addr = GET_ADDR(to_push);

  const int pt_bus = hyundai_can_canfd_blended ? 1 : 0;
  const int non_cam_scc_bus = hyundai_can_canfd_blended ? 1 : 0;
  const int scc_bus = hyundai_camera_scc ? 2 : non_cam_scc_bus;

  // SCC12 is on bus 2 for camera-based SCC cars, bus 0 on all others
  if ((addr == 0x421) && (bus == scc_bus)) {
    uint8_t cruise_byte = hyundai_can_canfd_blended ? (GET_BYTE(to_push, 3) >> 4) : (GET_BYTES(to_push, 0, 4) >> 13);
    bool cruise_engaged = (cruise_byte & 0x3U) != 0U;
    hyundai_common_cruise_state_check(cruise_engaged);
  }

  if (bus == pt_bus) {
    if (addr == 0x251) {
      int torque_driver_new = (GET_BYTES(to_push, 0, 2) & 0x7ffU) - 1024U;
      // update array of samples
      update_sample(&torque_driver, torque_driver_new);
    }

    // ACC steering wheel buttons
    if (addr == 0x4F1) {
      int cruise_button = GET_BYTE(to_push, 0) & 0x7U;
      bool main_button = GET_BIT(to_push, 3U);
      hyundai_common_cruise_buttons_check(cruise_button, main_button);
    }

    // gas press, different for EV, hybrid, and ICE models
    if ((addr == 0x371) && hyundai_ev_gas_signal) {
      gas_pressed = (((GET_BYTE(to_push, 4) & 0x7FU) << 1) | GET_BYTE(to_push, 3) >> 7) != 0U;
    } else if ((addr == 0x371) && hyundai_hybrid_gas_signal) {
      gas_pressed = GET_BYTE(to_push, 7) != 0U;
    } else if ((addr == 0x260) && !hyundai_ev_gas_signal && !hyundai_hybrid_gas_signal) {
      gas_pressed = (GET_BYTE(to_push, 7) >> 6) != 0U;
    } else {
    }

    // sample wheel speed, averaging opposite corners
    if (addr == 0x386) {
      uint32_t front_left_speed = GET_BYTES(to_push, 0, 2) & 0x3FFFU;
      uint32_t rear_right_speed = GET_BYTES(to_push, 6, 2) & 0x3FFFU;
      vehicle_moving = (front_left_speed > HYUNDAI_STANDSTILL_THRSLD) || (rear_right_speed > HYUNDAI_STANDSTILL_THRSLD);
    }

    if (addr == 0x394) {
      brake_pressed = ((GET_BYTE(to_push, 5) >> 5U) & 0x3U) == 0x2U;
    }
  }

  hyundai_common_reset_acc_main_on_mismatches();
}

static bool hyundai_tx_hook(const CANPacket_t *to_send) {
  const TorqueSteeringLimits HYUNDAI_STEERING_LIMITS = HYUNDAI_LIMITS(384, 3, 7, 50);
  const TorqueSteeringLimits HYUNDAI_STEERING_LIMITS_ALT = HYUNDAI_LIMITS(270, 2, 3, 50);
  const TorqueSteeringLimits HYUNDAI_STEERING_LIMITS_ALT_2 = HYUNDAI_LIMITS(170, 2, 3, 50);
  const TorqueSteeringLimits HYUNDAI_STEERING_LIMITS_CAN_CANFD_BLENDED = HYUNDAI_LIMITS(384, 2, 3, 250);

  bool tx = true;
  int addr = GET_ADDR(to_send);

  // FCA11: Block any potential actuation
  if ((addr == 0x38D) && !hyundai_can_canfd_blended) {
    int CR_VSM_DecCmd = GET_BYTE(to_send, 1);
    bool FCA_CmdAct = GET_BIT(to_send, 20U);
    bool CF_VSM_DecCmdAct = GET_BIT(to_send, 31U);

    if ((CR_VSM_DecCmd != 0) || FCA_CmdAct || CF_VSM_DecCmdAct) {
      tx = false;
    }
  }

  // ACCEL: safety check
  if (((addr == 0x420) && hyundai_can_canfd_blended) || ((addr == 0x421) && !hyundai_can_canfd_blended)) {
    int desired_accel_raw = hyundai_can_canfd_blended ? (((GET_BYTE(to_send, 4) & 0x3FU) << 5) | (GET_BYTE(to_send, 3) >> 3)) - 1023U :
                                                            (((GET_BYTE(to_send, 4) & 0x7U) << 8) | GET_BYTE(to_send, 3)) - 1023U;
    int desired_accel_val = hyundai_can_canfd_blended ? (((GET_BYTE(to_send, 3) & 0x7U) << 8) | GET_BYTE(to_send, 2)) - 1023U :
                                                            ((GET_BYTE(to_send, 5) << 3) | (GET_BYTE(to_send, 4) >> 5)) - 1023U;

    int aeb_decel_cmd = hyundai_can_canfd_blended ? 0 : GET_BYTE(to_send, 2);
    bool aeb_req = hyundai_can_canfd_blended ? 0 : GET_BIT(to_send, 54U);

    bool violation = false;

    violation |= longitudinal_accel_checks(desired_accel_raw, HYUNDAI_LONG_LIMITS);
    violation |= longitudinal_accel_checks(desired_accel_val, HYUNDAI_LONG_LIMITS);
    violation |= (aeb_decel_cmd != 0);
    violation |= aeb_req;

    if (violation) {
      tx = false;
    }
  }

  // LKA STEER: safety check
  if ((addr == 0x340) && !hyundai_can_canfd_blended) {
    int desired_torque = ((GET_BYTES(to_send, 0, 4) >> 16) & 0x7ffU) - 1024U;
    bool steer_req = GET_BIT(to_send, 27U);

    const TorqueSteeringLimits limits = hyundai_alt_limits_2 ? HYUNDAI_STEERING_LIMITS_ALT_2 :
                                        hyundai_alt_limits ? HYUNDAI_STEERING_LIMITS_ALT : HYUNDAI_STEERING_LIMITS;

    if (steer_torque_cmd_checks(desired_torque, steer_req, limits)) {
      tx = false;
    }
  }

  // CAN CAN-FD Hybrid steering
  if (addr == 0x50) {
    int desired_torque = (((GET_BYTE(to_send, 6) & 0xFU) << 7U) | (GET_BYTE(to_send, 5) >> 1U)) - 1024U;
    bool steer_req = GET_BIT(to_send, 52U);

    if (steer_torque_cmd_checks(desired_torque, steer_req, HYUNDAI_STEERING_LIMITS)) {
      tx = false;
    }
  }

  // UDS: Only tester present ("\x02\x3E\x80\x00\x00\x00\x00\x00") allowed on diagnostics address
  if ((addr == 0x7D0) || (addr == 0x730)) {
    if ((GET_BYTES(to_send, 0, 4) != 0x00803E02U) || (GET_BYTES(to_send, 4, 4) != 0x0U)) {
      tx = false;
    }
  }

  // BUTTONS: used for resume spamming and cruise cancellation
  if ((addr == 0x4F1) && !hyundai_longitudinal) {
    int button = GET_BYTE(to_send, 0) & 0x7U;

    bool allowed_resume = (button == 1) && controls_allowed;
    bool allowed_cancel = (button == 4) && cruise_engaged_prev;
    if (!(allowed_resume || allowed_cancel)) {
      tx = false;
    }
  }

  return tx;
}

static safety_config hyundai_init(uint16_t param) {
  // static const CanMsg HYUNDAI_LONG_TX_MSGS[] = {
  //   HYUNDAI_LONG_COMMON_TX_MSGS(0)
  //   {0x38D, 0, 8, .check_relay = false}, // FCA11 Bus 0
  //   {0x483, 0, 8, .check_relay = false}, // FCA12 Bus 0
  //   {0x7D0, 0, 8, .check_relay = false}, // radar UDS TX addr Bus 0 (for radar disable)
  // };

  // static const CanMsg HYUNDAI_CAMERA_SCC_TX_MSGS[] = {
  //   HYUNDAI_COMMON_TX_MSGS(2)
  // };

  // static const CanMsg HYUNDAI_CAMERA_SCC_LONG_TX_MSGS[] = {
  //   HYUNDAI_LONG_COMMON_TX_MSGS(2)
  // };

  // static const CanMsg HYUNDAI_LONG_ESCC_TX_MSGS[] = {
  //   HYUNDAI_LONG_COMMON_TX_MSGS(0)
  // };

  hyundai_common_init(param);
  hyundai_legacy = false;
  hyundai_can_canfd_blended = true;

  if (hyundai_can_canfd_blended) {
    gen_crc_lookup_table_16(0x1021, hyundai_canfd_crc_lut);
  }

  safety_config ret;
  if (hyundai_longitudinal) {
    ret = BUILD_SAFETY_CFG(hyundai_can_canfd_blended_hda2_long_rx_checks, HYUNDAI_CAN_CANFD_BLENDED_HDA2_LONG_TX_MSGS);
  // TODO: should just be hyundai_hda2
  } else if (hyundai_can_canfd_blended) {
    ret = BUILD_SAFETY_CFG(hyundai_can_canfd_blended_hda2_rx_checks, HYUNDAI_CAN_CANFD_BLENDED_HDA2_TX_MSGS);
  } else {
    ret = BUILD_SAFETY_CFG(hyundai_rx_checks, HYUNDAI_TX_MSGS);
  }
  return ret;
}

static safety_config hyundai_legacy_init(uint16_t param) {
  // older hyundai models have less checks due to missing counters and checksums
  static RxCheck hyundai_legacy_rx_checks[] = {
    HYUNDAI_COMMON_RX_CHECKS(true, false, 0)
    HYUNDAI_SCC12_ADDR_CHECK(false, 0)
    HYUNDAI_SCC11_ADDR_CHECK(0)
  };

  hyundai_common_init(param);
  hyundai_legacy = true;
  hyundai_longitudinal = false;
  hyundai_camera_scc = false;
  return BUILD_SAFETY_CFG(hyundai_legacy_rx_checks, HYUNDAI_TX_MSGS);
}

const safety_hooks hyundai_hooks = {
  .init = hyundai_init,
  .rx = hyundai_rx_hook,
  .tx = hyundai_tx_hook,
  .get_counter = hyundai_get_counter,
  .get_checksum = hyundai_get_checksum,
  .compute_checksum = hyundai_compute_checksum,
};

const safety_hooks hyundai_legacy_hooks = {
  .init = hyundai_legacy_init,
  .rx = hyundai_rx_hook,
  .tx = hyundai_tx_hook,
  .get_counter = hyundai_get_counter,
  .get_checksum = hyundai_get_checksum,
  .compute_checksum = hyundai_compute_checksum,
};
