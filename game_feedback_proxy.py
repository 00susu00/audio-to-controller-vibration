#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏原生震动代理。

把实体 XInput 手柄的输入状态镜像到一个 ViGEm/vgamepad 虚拟 Xbox 360 手柄，
游戏向虚拟手柄发送的震动请求会通过 notification 回调交给 ControllerManager。

重要：
- 该代理负责“输入镜像 + 游戏震动回调”，不直接向实体手柄发送震动。
- 为确保游戏只使用虚拟手柄，Windows 上通常需要 HidHide 隐藏实体手柄，
  并把本程序/Python 加入 HidHide 的允许列表。
"""

import threading
import time


class GameFeedbackProxy:
    """实体 XInput -> 虚拟 X360 的低延迟代理。"""

    def __init__(self, controller_manager, physical_controller_id, poll_hz=250):
        self.controller_manager = controller_manager
        self.physical_controller_id = int(physical_controller_id)
        self.poll_hz = max(60, min(1000, int(poll_hz)))

        self.virtual_gamepad = None
        self.virtual_controller_id = None
        self._xinput = None
        self._vg = None

        self._thread = None
        self._stop_event = threading.Event()
        self._running = False
        self._last_packet_number = None
        self._last_input_time = 0.0
        self._last_error = None
        self._mirror_updates = 0

    @staticmethod
    def _enumerate_xinput_slots(xinput_module):
        slots = set()
        for controller_id in range(4):
            try:
                xinput_module.get_state(controller_id)
                slots.add(controller_id)
            except Exception:
                pass
        return slots

    def _resolve_virtual_controller_id(self, before_slots):
        """尽量识别新出现的虚拟 XInput 槽位，便于扫描/强制震动时排除它。"""
        deadline = time.time() + 0.6
        while time.time() < deadline:
            after_slots = self._enumerate_xinput_slots(self._xinput)
            new_slots = sorted(after_slots - before_slots)
            if len(new_slots) == 1:
                return new_slots[0]
            time.sleep(0.02)

        # vgamepad.get_index() 是 ViGEm 内部 target index，不保证等于 XInput
        # user index，因此不能拿它来排除某个 XInput 槽位。识别不唯一时保持 None，
        # 比误判实体手柄更安全。
        return None

    def start(self):
        if self._running:
            return True

        try:
            import XInput
            import vgamepad as vg
        except ImportError as exc:
            self._last_error = (
                f"缺少游戏震动代理依赖: {exc}. "
                "请运行 pip install vgamepad XInput-Python"
            )
            print(f"⚠️ {self._last_error}")
            return False

        self._xinput = XInput
        self._vg = vg

        try:
            # 必须在创建虚拟手柄之前固定实体手柄槽位，避免把新虚拟手柄误当实体设备。
            self._xinput.get_state(self.physical_controller_id)
            before_slots = self._enumerate_xinput_slots(self._xinput)

            self.virtual_gamepad = vg.VX360Gamepad()
            if not self.controller_manager.attach_game_feedback_source(self.virtual_gamepad):
                raise RuntimeError("无法注册虚拟手柄震动回调")

            self.virtual_controller_id = self._resolve_virtual_controller_id(before_slots)

            self._stop_event.clear()
            self._running = True
            self._thread = threading.Thread(
                target=self._mirror_loop,
                name="GameFeedbackProxy",
                daemon=True,
            )
            self._thread.start()

            virtual_text = (
                str(self.virtual_controller_id)
                if self.virtual_controller_id is not None
                else "已创建(槽位未识别)"
            )
            print(
                "✓ 游戏原生震动代理已启动: "
                f"实体 XInput {self.physical_controller_id} -> 虚拟 XInput {virtual_text}, "
                f"{self.poll_hz} Hz"
            )
            print(
                "  提示: 要稳定捕获游戏震动，请让游戏使用虚拟手柄；"
                "推荐用 HidHide 对游戏隐藏实体手柄，并允许本程序访问实体手柄。"
            )
            return True

        except Exception as exc:
            self._last_error = str(exc)
            print(f"⚠️ 游戏原生震动代理启动失败: {exc}")
            self.stop()
            return False

    def _copy_state_to_virtual(self, state):
        gamepad = state.Gamepad

        # XInput 与 ViGEm X360 的按键 bit mask 相同，可直接镜像。
        self.virtual_gamepad.report.wButtons = int(gamepad.wButtons)
        self.virtual_gamepad.left_trigger(value=int(gamepad.bLeftTrigger))
        self.virtual_gamepad.right_trigger(value=int(gamepad.bRightTrigger))
        self.virtual_gamepad.left_joystick(
            x_value=int(gamepad.sThumbLX),
            y_value=int(gamepad.sThumbLY),
        )
        self.virtual_gamepad.right_joystick(
            x_value=int(gamepad.sThumbRX),
            y_value=int(gamepad.sThumbRY),
        )
        self.virtual_gamepad.update()

    def _mirror_loop(self):
        interval = 1.0 / float(self.poll_hz)
        reset_sent = False

        while not self._stop_event.is_set():
            loop_start = time.perf_counter()
            try:
                state = self._xinput.get_state(self.physical_controller_id)
                packet_number = int(state.dwPacketNumber)

                # XInput packet number 只在输入发生变化时增加。
                # 跳过重复 report 可以显著降低 Python/ViGEm 调用开销。
                if packet_number != self._last_packet_number:
                    self._copy_state_to_virtual(state)
                    self._last_packet_number = packet_number
                    self._mirror_updates += 1

                self._last_input_time = time.time()
                self._last_error = None
                reset_sent = False

            except Exception as exc:
                self._last_error = str(exc)
                # 实体手柄临时断开时，让虚拟手柄回到中立状态，避免按键/摇杆卡住。
                if self.virtual_gamepad is not None and not reset_sent:
                    try:
                        self.virtual_gamepad.reset()
                        self.virtual_gamepad.update()
                        reset_sent = True
                    except Exception:
                        pass

            elapsed = time.perf_counter() - loop_start
            remaining = interval - elapsed
            if remaining > 0:
                self._stop_event.wait(remaining)

    def get_status(self):
        input_age = (
            time.time() - self._last_input_time
            if self._last_input_time > 0
            else float("inf")
        )
        return {
            "running": self._running,
            "physical_controller_id": self.physical_controller_id,
            "virtual_controller_id": self.virtual_controller_id,
            "poll_hz": self.poll_hz,
            "last_input_age": input_age,
            "mirror_updates": self._mirror_updates,
            "last_error": self._last_error,
        }

    def stop(self):
        self._running = False
        self._stop_event.set()

        thread = self._thread
        self._thread = None
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=0.5)

        if (
            self.virtual_gamepad is not None
            and getattr(self.controller_manager, "game_feedback_provider", None)
            is self.virtual_gamepad
        ):
            self.controller_manager.detach_game_feedback_source()

        if self.virtual_gamepad is not None:
            try:
                self.virtual_gamepad.reset()
                self.virtual_gamepad.update()
            except Exception:
                pass

        # 释放最后一个 Python 引用后，vgamepad 会把虚拟设备从 ViGEmBus 移除。
        self.virtual_gamepad = None
        self.virtual_controller_id = None
        self._last_packet_number = None

    @property
    def is_running(self):
        return self._running
