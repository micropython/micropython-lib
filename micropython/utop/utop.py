import micropython
import time

try:
    import esp32
    import _thread
except ImportError:
    esp32 = None


def top(update_interval_ms=1000, timeout_ms=None, thread_names={}):
    time_start = time.ticks_ms()
    previous_total_runtime = None
    previous_task_runtimes = {}
    previous_line_count = 0
    esp32_task_state_names = dict(
        enumerate(("running", "ready", "blocked", "suspended", "deleted", "invalid"))
    )

    while timeout_ms is None or abs(time.ticks_diff(time.ticks_ms(), time_start)) < timeout_ms:
        if previous_line_count > 0:
            print("\x1b[{}A".format(previous_line_count), end="")
        line_count = 0

        if esp32 is not None:
            if not hasattr(esp32, "idf_task_info"):
                print(
                    "INFO: esp32.idf_task_info() is not available, cannot list active tasks.\x1b[K"
                )
                line_count += 1
            else:
                print("   CPU%  CORE  PRIORITY  STATE      STACKWATERMARK  NAME\x1b[K")
                line_count += 1

                total_runtime, tasks = esp32.idf_task_info()
                current_thread_id = _thread.get_ident()
                tasks.sort(key=lambda t: t[0])
                for (
                    task_id,
                    task_name,
                    task_state,
                    task_priority,
                    task_runtime,
                    task_stackhighwatermark,
                    task_coreid,
                ) in tasks:
                    task_runtime_percentage = "-"
                    if (
                        total_runtime != previous_total_runtime
                        and task_id in previous_task_runtimes
                    ):
                        task_runtime_percentage = "{:.2f}%".format(
                            100
                            * ((task_runtime - previous_task_runtimes[task_id]) & (2**32 - 1))
                            / ((total_runtime - previous_total_runtime) & (2**32 - 1))
                        )
                    print(
                        "{:>7}  {:>4}  {:>8d}  {:<9}  {:<14d}  {}{}\x1b[K".format(
                            task_runtime_percentage,
                            "-" if task_coreid is None else task_coreid,
                            task_priority,
                            esp32_task_state_names.get(task_state, "unknown"),
                            task_stackhighwatermark,
                            thread_names.get(task_id, task_name),
                            " (*)" if task_id == current_thread_id else "",
                        )
                    )
                    line_count += 1

                    previous_task_runtimes[task_id] = task_runtime
                previous_total_runtime = total_runtime
        else:
            print("INFO: Platform does not support listing active tasks.\x1b[K")
            line_count += 1

        print("\x1b[K")
        line_count += 1
        print("MicroPython ", end="")
        micropython.mem_info()
        line_count += 3

        if esp32 is not None:
            print("\x1b[K")
            line_count += 1
            for name, cap in (("data", esp32.HEAP_DATA), ("exec", esp32.HEAP_EXEC)):
                heaps = esp32.idf_heap_info(cap)
                print(
                    "IDF heap ({}): {} regions, {} total, {} free, {} largest contiguous, {} min free watermark\x1b[K".format(
                        name,
                        len(heaps),
                        sum((h[0] for h in heaps)),
                        sum((h[1] for h in heaps)),
                        max((h[2] for h in heaps)),
                        sum((h[3] for h in heaps)),
                    )
                )
                line_count += 1

        if previous_line_count > line_count:
            for _ in range(previous_line_count - line_count):
                print("\x1b[K")
            print("\x1b[{}A".format(previous_line_count - line_count), end="")

        previous_line_count = line_count

        try:
            time.sleep_ms(update_interval_ms)
        except KeyboardInterrupt:
            break
