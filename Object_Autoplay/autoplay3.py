from pymol import cmd
import threading
import time

# 获取所有加载的 object 名称
all_objs = cmd.get_object_list()
stored = {'index': 0, 'paused': False}

# 显示当前 object
def show_object(index):
    cmd.disable()
    cmd.enable(all_objs[index])
    print(f"▶️ Now showing: {all_objs[index]}")

# 下一个 object
def next_object():
    stored['index'] = (stored['index'] + 1) % len(all_objs)
    show_object(stored['index'])

# 上一个 object
def prev_object():
    stored['index'] = (stored['index'] - 1) % len(all_objs)
    show_object(stored['index'])

# 暂停/恢复
def toggle_pause():
    stored['paused'] = not stored['paused']
    print("⏸ Paused" if stored['paused'] else "▶️ Resumed")

# 打印当前 object 名字
def print_current_object():
    print(f"🔍 当前显示: {all_objs[stored['index']]}")



# 设置快捷键：→ ← F5
cmd.set_key('right', lambda: next_object())
cmd.set_key('left', lambda: prev_object())
cmd.set_key('F5', lambda: toggle_pause())  # 使用 F5 控制暂停
cmd.set_key('F6', lambda: print_current_object()) # 使用 F6 打印当前 object 名字

# 自动切换线程
def auto_loop():
    while True:
        time.sleep(2)
        if not stored['paused']:
            cmd.lock()
            try:
                next_object()
            finally:
                cmd.unlock()

# 初始化显示第一个 object
show_object(stored['index'])

# 启动后台线程
threading.Thread(target=auto_loop, daemon=True).start()

print("✅ 自动播放中：每5秒切换一次 object")
print("➡️ 右键下一个，⬅️ 左键上一个，🕹️ F5 暂停/继续")
