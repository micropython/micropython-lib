# MicroPython LoRa async modem driver
# MIT license; Copyright (c) 2023 Angus Gratton
#
# LoRa is a registered trademark or service mark of Semtech Corporation or its affiliates.

import asyncio
import time
from micropython import const

# Set to True to get some additional printed debug output.
_DEBUG = const(False)

# Some "belts and braces" timeouts when using IRQs, to wake up if an IRQ hasn't
# fired as expected. Also a timeout for how rapidly to poll the modem during TX
# if no IRQ is enabled.
#
# All in milliseconds
_RX_POLL_WITH_IRQ = const(1000)
_RX_POLL_NO_IRQ = const(50)
_TX_POLL_LATE_IRQ = const(10)


class AsyncModem:
    # Mixin-like base class that provides coroutines for modem send, recv & recv_continuous.
    #
    # Don't instantiate this class directly, instantiate one of the 'AsyncXYZ'
    # modem classes defined in the lora module.

    def _after_init(self):
        # Separate flags for (rx, tx) as only one task can block on a flag
        self._flags = (asyncio.ThreadSafeFlag(), asyncio.ThreadSafeFlag())
        self.set_irq_callback(self._callback)

    async def recv(self, timeout_ms=None, rx_length=0xFF, rx_packet=None):
        # Async function to receive a single LoRa packet, with an optional timeout
        #
        # Same API as the "Simple API" synchronous function
        self._flags[0].clear()
        will_irq = self.start_recv(timeout_ms, False, rx_length)
        return await self._recv(will_irq, rx_packet)

    def recv_continuous(self, rx_length=0xFF, rx_packet=None):
        # Returns an Async Iterator that continuously yields LoRa packets, until
        # the modem is told to sleep() or standby().
        #
        # Once MicroPython has PEP525 support (PR #6668) then this somewhat
        # fiddly implementation can probably be merged with recv() into a much simpler
        # single _recv() private coro that either yields or returns, depending on
        # an argument. The public API can stay the same.
        will_irq = self.start_recv(None, True, rx_length)
        return AsyncContinuousReceiver(self, will_irq, rx_packet)

    async def _recv(self, will_irq, rx_packet):
        # Second half of receiving is implemented here to share code with AsyncContinuousReceiver,
        # until future refactor is possible (see comment immediately above this one.)
        rx = True
        while rx is True:
            await self._wait(will_irq, 0, _RX_POLL_WITH_IRQ if will_irq else _RX_POLL_NO_IRQ)
            rx = self.poll_recv(rx_packet)
        if rx:  # RxPacket instance
            return rx

    async def send(self, packet, tx_at_ms=None):
        self._flags[1].clear()
        self.prepare_send(packet)

        timeout_ms = self.get_time_on_air_us(len(packet)) // 1000 + 50

        if tx_at_ms is not None:
            await asyncio.sleep_ms(max(0, time.ticks_diff(tx_at_ms, time.ticks_ms())))

        if _DEBUG:
            print("start_send")

        will_irq = self.start_send()

        tx = True
        while tx is True:
            await self._wait(will_irq, 1, timeout_ms)
            tx = self.poll_send()

            if _DEBUG:
                print(f"poll_send returned tx={tx}")

            # If we've already waited the estimated send time (plus 50ms) and the modem
            # is not done, timeout and poll more rapidly from here on (unsure if
            # this is necessary, outside of a serious bug, but doesn't hurt.)
            timeout_ms = _TX_POLL_LATE_IRQ

        return tx

    async def _wait(self, will_irq, idx, timeout_ms):
        # Common code path for blocking on an interrupt, if configured.
        #
        # idx is into _flags tuple and is 0 for rx and 1 for tx
        #
        # timeout_ms is the expected send time for sends, or a reasonable
        # polling timeout for receives.
        if _DEBUG:
            print(f"wait will_irq={will_irq} timeout_ms={timeout_ms}")
        if will_irq:
            # In theory we don't need to ever timeout on the flag as the ISR will always
            # fire, but this gives a workaround for possible race conditions or dropped interrupts.
            try:
                await asyncio.wait_for_ms(self._flags[idx].wait(), timeout_ms)
            except asyncio.TimeoutError:
                pass
        else:
            await asyncio.sleep_ms(timeout_ms)

        if _DEBUG:
            print("wait complete")

    def _callback(self):
        # IRQ callback from BaseModem._radio_isr. May be in Hard IRQ context.
        #
        # Set both RX & TX flag. This isn't necessary for "real" interrupts, but may be necessary
        # to wake both for the case of a "soft" interrupt triggered by sleep() or standby(), where
        # both tasks need to unblock and return.
        #
        # The poll_recv() method is a no-op if _tx is set, so waking up both
        # blocked tasks doesn't have much overhead (no second polling of modem
        # IRQ flags, for example).
        for f in self._flags:
            f.set()


class AsyncContinuousReceiver:
    # Stop-gap async iterator implementation until PEP525 support comes in, see
    # longer comment  on AsyncModem.recv_continuous() above.
    def __init__(self, modem, will_irq, rx_packet):
        self.modem = modem
        self.will_irq = will_irq
        self.rx_packet = rx_packet

    def __aiter__(self):
        return self

    async def __anext__(self):
        res = await self.modem._recv(self.will_irq, self.rx_packet)
        if not res:
            raise StopAsyncIteration
        return res
