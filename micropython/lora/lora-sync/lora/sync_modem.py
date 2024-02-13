# MicroPython LoRa synchronous modem driver
# MIT license; Copyright (c) 2023 Angus Gratton
#
# LoRa is a registered trademark or service mark of Semtech Corporation or its affiliates.

import machine
import time


class SyncModem:
    # Mixin-like base class that provides synchronous modem send and recv
    # functions
    #
    #
    # Don't instantiate this class directly, instantiate one of the 'AsyncXYZ'
    # modem classes defined in the lora module.
    #
    # These are intended for simple applications. They block the caller until
    # the modem operation is complete, and don't support interleaving send
    # and receive.

    def _after_init(self):
        pass  # Needed for AsyncModem but not SyncModem

    def send(self, packet, tx_at_ms=None):
        # Send the given packet (byte sequence),
        # and return once transmission of the packet is complete.
        #
        # Returns a timestamp (result of time.ticks_ms()) when the packet
        # finished sending.
        self.prepare_send(packet)

        # If the caller specified a timestamp to start transmission at, wait until
        # that time before triggering the send
        if tx_at_ms is not None:
            time.sleep_ms(max(0, time.ticks_diff(tx_at_ms, time.ticks_ms())))

        will_irq = self.start_send()  # ... and go!

        # sleep for the expected send time before checking if send has ended
        time.sleep_ms(self.get_time_on_air_us(len(packet)) // 1000)

        tx = True
        while tx is True:
            self._sync_wait(will_irq)
            tx = self.poll_send()
        return tx

    def recv(self, timeout_ms=None, rx_length=0xFF, rx_packet=None):
        # Attempt to a receive a single LoRa packet, timeout after timeout_ms milliseconds
        # or wait indefinitely if no timeout is supplied (default).
        #
        # Returns an instance of RxPacket or None if the radio timed out while receiving.
        #
        # Optional rx_length argument is only used if lora_cfg["implict_header"] == True
        # (not the default) and holds the length of the payload to receive.
        #
        # Optional rx_packet argument can be an existing instance of RxPacket
        # which will be reused to save allocations, but only if the received packet
        # is the same length as the rx_packet packet. If the length is different, a
        # new RxPacket instance is allocated and returned.
        will_irq = self.start_recv(timeout_ms, False, rx_length)
        rx = True
        while rx is True:
            self._sync_wait(will_irq)
            rx = self.poll_recv(rx_packet)
        return rx or None

    def _sync_wait(self, will_irq):
        # For synchronous usage, block until an interrupt occurs or we time out
        if will_irq:
            for n in range(100):
                machine.idle()
                # machine.idle() wakes up very often, so don't actually return
                # unless _radio_isr ran already. The outer for loop is so the
                # modem is still polled occasionally to
                # avoid the possibility an IRQ was lost somewhere.
                #
                # None of this is very efficient, power users should either use
                # async or call the low-level API manually with better
                # port-specific sleep configurations, in order to get the best
                # efficiency.
                if self.irq_triggered():
                    break
        else:
            time.sleep_ms(1)
