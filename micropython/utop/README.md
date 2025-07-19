# utop

Provides a top-like live overview of the running system.

On the `esp32` port this depends on the `esp32.idf_task_info()` function, which
can be enabled by adding the following lines to the board `sdkconfig`:

```ini
CONFIG_FREERTOS_USE_TRACE_FACILITY=y
CONFIG_FREERTOS_VTASKLIST_INCLUDE_COREID=y
CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS=y
```
