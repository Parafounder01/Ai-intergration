#!/usr/bin/env python3
"""
@autobot — 30ms Ultra-Fast Automation Demo
Tests PyAutoGUI speed at 30ms (0.03s) intervals
"""

import subprocess
import time
import math
import pyautogui as pg
import sys
import io

# ── Fix UTF-8 encoding for Windows console ──
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Timing wrapper ──
timings = {}

def step(name, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = (time.perf_counter() - start) * 1000  # ms
    timings[name] = round(elapsed, 2)
    print(f"  ⏱️  {name}: {timings[name]:.2f}ms")
    return result

def center_screen():
    w, h = pg.size()
    return w // 2, h // 2

print("=" * 55)
print("  ⚡ @AUTOBOT — 30ms SPEED TEST ⚡")
print("=" * 55)

# ── 1. Open Notepad ──
print("\n📂 Step 1: Opening Notepad...")
step("Open Notepad", lambda: subprocess.Popen('notepad.exe'))

# Give Notepad time to launch
time.sleep(1.5)

# ── 2. First message at 30ms ──
print("\n⌨️  Step 2: Typing '30ms speed test - autobot fast!' @ 30ms...")
step("Type Message 1", lambda: pg.write("30ms speed test - autobot fast!", interval=0.03))

# ── 3. Wait 1 second ──
print("\n⏸️  Step 3: Waiting 1 second...")
time.sleep(1)
print("  ✅ Wait complete")

# ── 4. Second message at 30ms ──
print("\n⌨️  Step 4: Typing 'Hello from autobot @ 30ms!' @ 30ms...")
step("Type Message 2", lambda: pg.write("Hello from autobot @ 30ms!", interval=0.03))

# ── 5. Mouse circle at 30ms ──
print("\n🖱️  Step 5: Moving mouse in 3 circles @ 30ms...")
cx, cy = center_screen()
radius = 50
steps_per_loop = 36  # 36 points per circle = every 10 degrees
total_steps = steps_per_loop * 3  # 3 loops

def draw_circles():
    for i in range(total_steps):
        angle = 2 * math.pi * i / steps_per_loop
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        pg.moveTo(x, y, duration=0.03)

step("Mouse Circles", draw_circles)

# ── Final Report ──
print("\n" + "=" * 55)
print("  📊 FINAL TIMING REPORT")
print("=" * 55)
for name, ms in timings.items():
    print(f"  {name:25s} → {ms:>8.2f} ms")

total = sum(timings.values())
print(f"  {'TOTAL':25s} → {total:>8.2f} ms")
print(f"  {'TOTAL (seconds)':25s} → {total/1000:>8.2f} s")
print("=" * 55)
print("  ✅ @autobot 30ms speed test COMPLETE! 🔥")
print("=" * 55)
