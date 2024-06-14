import gc
import time

try:
    import esp32
except ImportError:
    esp32 = None


def top(update_interval_ms=1000, timeout_ms=None):
    time_start = time.ticks_ms()
    previous_total_runtime = None
    previous_task_runtimes = {}
    previous_line_count = 0
    esp32_task_state_names = ("running", "ready", "blocked", "suspended", "deleted", "invalid")

    while timeout_ms is None or abs(time.ticks_diff(time.ticks_ms(), time_start)) < timeout_ms:
        if previous_line_count > 0:
            print("\x1B[{}A".format(previous_line_count), end="")
        line_count = 0

        if esp32 is not None:
            if not hasattr(esp32, "idf_task_stats"):
                print(
                    "INFO: esp32.idf_task_stats() is not available, cannot list active tasks.\x1B[K"
                )
                line_count += 1
            else:
                print("   CPU%  CORE  PRIORITY  STATE      STACKWATERMARK  NAME\x1B[K")
                line_count += 1

                total_runtime, tasks = esp32.idf_task_stats()
                tasks.sort(key=lambda t: t[1])
                for (
                    task_name,
                    task_id,
                    task_state,
                    task_priority,
                    task_runtime,
                    task_stackhighwatermark,
                    task_coreid,
                ) in tasks:
                    task_runtime_percentage = "-"
                    if total_runtime > 0:
                        if (
                            previous_total_runtime is not None
                            and task_id in previous_task_runtimes
                        ):
                            task_cpu_percentage = (
                                100
                                * (task_runtime - previous_task_runtimes[task_id])
                                / (total_runtime - previous_total_runtime)
                            )
                        else:
                            task_cpu_percentage = 100 * task_runtime / total_runtime
                        task_runtime_percentage = "{:.2f}%".format(task_cpu_percentage)
                    task_state_name = "unknown"
                    if task_state >= 0 and task_state < len(esp32_task_state_names):
                        task_state_name = esp32_task_state_names[task_state]

                    print(
                        "{:>7}  {:>4d}  {:>8d}  {:<9}  {:<14d}  {}\x1B[K".format(
                            task_runtime_percentage,
                            task_coreid,
                            task_priority,
                            task_state_name,
                            task_stackhighwatermark,
                            task_name,
                        )
                    )
                    line_count += 1

                    previous_task_runtimes[task_id] = task_runtime
        else:
            print("INFO: Platform does not support listing active tasks.\x1B[K")
            line_count += 1

        if esp32 is not None:
            print("\x1B[K")
            line_count += 1
            for name, cap in (("data", esp32.HEAP_DATA), ("exec", esp32.HEAP_EXEC)):
                heaps = esp32.idf_heap_info(cap)
                print(
                    "IDF heap ({}): {} regions, {} total, {} free, {} largest contiguous, {} min free watermark\x1B[K".format(
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
                print("\x1B[K")
            print("\x1B[{}A".format(previous_line_count - line_count), end="")

        previous_total_runtime = total_runtime
        previous_line_count = line_count

        time.sleep_ms(update_interval_ms)
