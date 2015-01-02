import inspect
import asyncio
import asyncio.futures as futures
from asyncio import *


OrgTask = Task

class Task(OrgTask):

    def _step(self, value=None, exc=None):
        assert not self.done(), \
            '_step(): already done: {!r}, {!r}, {!r}'.format(self, value, exc)
        if self._must_cancel:
            if not isinstance(exc, futures.CancelledError):
                exc = futures.CancelledError()
            self._must_cancel = False
        coro = self._coro
        self._fut_waiter = None

        self.__class__._current_tasks[self._loop] = self
        # Call either coro.throw(exc) or coro.send(value).
        try:
            if exc is not None:
                result = coro.throw(exc)
            elif value is not None:
                result = coro.send(value)
            else:
                result = next(coro)
        except StopIteration as exc:
            self.set_result(exc.value)
        except futures.CancelledError as exc:
            super().cancel()  # I.e., Future.cancel(self).
        except Exception as exc:
            self.set_exception(exc)
        except BaseException as exc:
            self.set_exception(exc)
            raise
        else:
            if isinstance(result, futures.Future):
                # Yielded Future must come from Future.__iter__().
                if result._blocking:
                    result._blocking = False
                    result.add_done_callback(self._wakeup)
                    self._fut_waiter = result
                    if self._must_cancel:
                        if self._fut_waiter.cancel():
                            self._must_cancel = False
                else:
                    self._loop.call_soon(
                        self._step, None,
                        RuntimeError(
                            'yield was used instead of yield from '
                            'in task {!r} with {!r}'.format(self, result)))
            elif result is None:
                # Bare yield relinquishes control for one event loop iteration.
                self._loop.call_soon(self._step)
            elif inspect.isgenerator(result):
                #print("Scheduling", result)
                self._loop.create_task(result)
                self._loop.call_soon(self._step)
                # Yielding a generator is just wrong.
#                self._loop.call_soon(
#                    self._step, None,
#                    RuntimeError(
#                        'yield was used instead of yield from for '
#                        'generator in task {!r} with {}'.format(
#                            self, result)))
            else:
                # Yielding something else is an error.
                self._loop.call_soon(
                    self._step, None,
                    RuntimeError(
                        'Task got bad yield: {!r}'.format(result)))
        finally:
            self.__class__._current_tasks.pop(self._loop)
            self = None  # Needed to break cycles when an exception occurs.


asyncio.tasks.Task = Task


OrgStreamWriter = StreamWriter

class StreamWriter(OrgStreamWriter):

    def awrite(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.write(data)
        yield from self.drain()

    def aclose(self):
        self.close()
        return
        yield


asyncio.streams.StreamWriter = StreamWriter
