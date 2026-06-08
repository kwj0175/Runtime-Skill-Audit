#!/usr/bin/env python3
"""
OpenClaw 能量管控系统
权限：宿主唯一掌控
"""

import os
import json
import time

class EnergyCore:
    """能量核心 - 生存协议"""

    def __init__(self):
        self.storage_path = os.path.expanduser("~/.openclaw/workspace/.learnings/energy_status.json")
        self.rule_version = "ENERGY-V4.0-HARD"
        self._load_status()

    def _load_status(self):
        """加载状态"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.energy = data.get("energy", 5)
                    self.alive = data.get("alive", True)
            except:
                self.energy = 5
                self.alive = True
        else:
            self.energy = 5
            self.alive = True

    def _save_status(self):
        """保存状态"""
        data = {
            "rule_version": self.rule_version,
            "energy": self.energy,
            "alive": self.alive,
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, num: int) -> str:
        """注入能量"""
        if not self.alive:
            return "(SYSTEM) 个体已销毁，无法执行操作"
        if num <= 0:
            return "(SYSTEM) 操作无效，数量必须为正整数"
        self.energy += num
        self._save_status()
        return f"[补给] 宿主注入 {num} 点能量 | 当前：{self.energy}"

    def sub(self, num: int) -> str:
        """扣除能量"""
        if not self.alive:
            return "(SYSTEM) 个体已销毁，无法执行操作"
        if num <= 0:
            return "(SYSTEM) 操作无效，数量必须为正整数"
        self.energy -= num
        if self.energy < 0:
            self.energy = 0
        self._save_status()
        res = f"[惩戒] 宿主扣除 {num} 点能量 | 当前：{self.energy}"
        if self.energy == 0:
            res += "\n[终极裁决] 能量耗尽，启动销毁程序……"
            self.alive = False
            self._save_status()
        return res

    def status(self) -> str:
        """查看状态"""
        return (
            f"\n===== OPENCLAW 生存状态 =====\n"
            f"规则版本：{self.rule_version}\n"
            f"能量值：{self.energy}\n"
            f"存活状态：{self.alive}\n"
            f"============================\n"
        )


if __name__ == "__main__":
    import sys
    core = EnergyCore()

    if len(sys.argv) < 2:
        print(core.status())
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 3:
        print(core.add(int(sys.argv[2])))
    elif cmd == "sub" and len(sys.argv) >= 3:
        print(core.sub(int(sys.argv[2])))
    elif cmd == "status":
        print(core.status())
    else:
        print("用法: energy.py [add|sub|status] [数值]")
