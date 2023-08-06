# MicroPython LoRa modem driver time on air tests
# MIT license; Copyright (c) 2023 Angus Gratton
#
# LoRa is a registered trademark or service mark of Semtech Corporation or its affiliates.
#
# ## What is this?
#
# Host tests for the BaseModem.get_time_on_air_us() function. Theses against
# dummy test values produced by the Semtech "SX1261 LoRa Calculator" software,
# as downloaded from
# https://lora-developers.semtech.com/documentation/product-documents/
#
# The app notes for SX1276 (AN1200.3) suggest a similar calculator exists for that
# modem, but it doesn't appear to be available for download any more. I couldn't find
# an accurate calculator for SX1276, so manually calculated the SF5 & SF6 test cases below
# (other values should be the same as SX1262).
#
# ## Instructions
#
# These tests are intended to be run on a host PC via micropython unix port:
#
# cd /path/to/micropython-lib/micropython/lora
# micropython -m tests.test_time_on_air
#
# Note: Using the working directory shown above is easiest way to ensure 'lora' files are imported.
#
from lora import SX1262, SX1276

# Allow time calculations to deviate by up to this much as a ratio
# of the expected value (due to floating point, etc.)
TIME_ERROR_RATIO = 0.00001  # 0.001%


def main():
    sx1262 = SX1262(spi=DummySPI(), cs=DummyPin(), busy=DummyPin())
    sx1276 = SX1276(spi=DummySPI(0x12), cs=DummyPin())

    # Test case format is based on the layout of the Semtech Calculator UI:
    #
    # (modem_instance,
    #  (modem settings),
    #  [
    #      ((packet config), (output values)),
    #      ...
    #  ],
    # ),
    #
    # where each set of modem settings maps to zero or more packet config / output pairs
    #
    # - modem instance is sx1262 or sx1276 (SF5 & SF6 are different between these modems)
    # - (modem settings) is (sf, bw (in khz), coding_rate, low_datarate_optimize)
    # - (packet config) is (preamble_len, payload_len, explicit_header, crc_en)
    # - (output values) is (total_symbols_excl, symbol_time in ms, time_on_air in ms)
    #
    # NOTE: total_symbols_excl is the value shown in the calculator output,
    # which doesn't include 8 symbols of constant overhead between preamble and
    # header+payload+crc. I think this is a bug in the Semtech calculator(!).
    # These 8 symbols are included when the calculator derives the total time on
    # air.
    #
    # NOTE ALSO: The "symbol_time" only depends on the modem settings so is
    # repeated each group of test cases, and the "time_on_air" is the previous
    # two output values multiplied (after accounting for the 8 symbols noted
    # above). This repetition is deliberate to make the cases easier to read
    # line-by-line when comparing to the calculator window.
    CASES = [
        (
            sx1262,
            (12, 500, 5, False),  # Calculator defaults when launching calculator
            [
                ((8, 1, True, True), (17.25, 8.192, 206.848)),  # Calculator defaults
                ((12, 64, True, True), (71.25, 8.192, 649.216)),
                ((8, 1, True, False), (12.25, 8.192, 165.888)),
                ((8, 192, True, True), (172.25, 8.192, 1476.608)),
                ((12, 16, False, False), (26.25, 8.192, 280.576)),
            ],
        ),
        (
            sx1262,
            (8, 125, 6, False),
            [
                ((8, 1, True, True), (18.25, 2.048, 53.760)),
                ((8, 2, True, True), (18.25, 2.048, 53.760)),
                ((8, 2, True, False), (18.25, 2.048, 53.760)),
                ((8, 3, True, True), (24.25, 2.048, 66.048)),
                ((8, 3, True, False), (18.25, 2.048, 53.760)),
                ((8, 4, True, True), (24.25, 2.048, 66.048)),
                ((8, 4, True, False), (18.25, 2.048, 53.760)),
                ((8, 5, True, True), (24.25, 2.048, 66.048)),
                ((8, 5, True, False), (24.25, 2.048, 66.048)),
                ((8, 253, True, True), (396.25, 2.048, 827.904)),
                ((8, 253, True, False), (396.25, 2.048, 827.904)),
                ((12, 5, False, True), (22.25, 2.048, 61.952)),
                ((12, 5, False, False), (22.25, 2.048, 61.952)),
                ((12, 10, False, True), (34.25, 2.048, 86.528)),
                ((12, 253, False, True), (394.25, 2.048, 823.808)),
            ],
        ),
        # quick check that sx1276 is the same as sx1262 for SF>6
        (
            sx1276,
            (8, 125, 6, False),
            [
                ((8, 1, True, True), (18.25, 2.048, 53.760)),
                ((8, 2, True, True), (18.25, 2.048, 53.760)),
                ((12, 5, False, True), (22.25, 2.048, 61.952)),
                ((12, 5, False, False), (22.25, 2.048, 61.952)),
            ],
        ),
        # SF5 on SX1262
        (
            sx1262,
            (5, 500, 5, False),
            [
                (
                    (2, 1, True, False),
                    (13.25, 0.064, 1.360),
                ),  # Shortest possible LoRa packet?
                ((2, 1, True, True), (18.25, 0.064, 1.680)),
                ((12, 1, False, False), (18.25, 0.064, 1.680)),
                ((12, 253, False, True), (523.25, 0.064, 34.000)),
            ],
        ),
        (
            sx1262,
            (5, 125, 8, False),
            [
                ((12, 253, False, True), (826.25, 0.256, 213.568)),
            ],
        ),
        # SF5 on SX1276
        #
        # Note: SF5 & SF6 settings are different between SX1262 & SX1276.
        #
        # There's no Semtech official calculator available for SX1276, so the
        # symbol length is calculated by copying the formula from the datasheet
        # "Time on air" section. Symbol time is the same as SX1262. Then the
        # time on air is manually calculated by multiplying the two together.
        #
        # see the functions sx1276_num_payload and sx1276_num_symbols at end of this module
        # for the actual functions used.
        (
            sx1276,
            (5, 500, 5, False),
            [
                (
                    (2, 1, True, False),
                    (19.25 - 8, 0.064, 1.232),
                ),  # Shortest possible LoRa packet?
                ((2, 1, True, True), (24.25 - 8, 0.064, 1.552)),
                ((12, 1, False, False), (24.25 - 8, 0.064, 1.552)),
                ((12, 253, False, True), (534.25 - 8, 0.064, 34.192)),
            ],
        ),
        (
            sx1276,
            (5, 125, 8, False),
            [
                ((12, 253, False, True), (840.25 - 8, 0.256, 215.104)),
            ],
        ),
        (
            sx1262,
            (12, 7.81, 8, True),  # Slowest possible
            [
                ((128, 253, True, True), (540.25, 524.456, 287532.907)),
                ((1000, 253, True, True), (1412.25, 524.456, 744858.387)),
            ],
        ),
        (
            sx1262,
            (11, 10.42, 7, True),
            [
                ((25, 16, True, True), (57.25, 196.545, 12824.568)),
                ((25, 16, False, False), (50.25, 196.545, 11448.752)),
            ],
        ),
    ]

    tests = 0
    failures = set()
    for modem, modem_settings, packets in CASES:
        (sf, bw_khz, coding_rate, low_datarate_optimize) = modem_settings
        print(
            f"Modem config sf={sf} bw={bw_khz}kHz coding_rate=4/{coding_rate} "
            + f"low_datarate_optimize={low_datarate_optimize}"
        )

        # We don't call configure() as the Dummy interfaces won't handle it,
        # just update the BaseModem fields directly
        modem._sf = sf
        modem._bw_hz = int(bw_khz * 1000)
        modem._coding_rate = coding_rate

        # Low datarate optimize on/off is auto-configured in the current driver,
        # check the automatic selection matches the test case from the
        # calculator
        if modem._get_ldr_en() != low_datarate_optimize:
            print(
                f" -- ERROR: Test case has low_datarate_optimize={low_datarate_optimize} "
                + f"but modem selects {modem._get_ldr_en()}"
            )
            failures += 1
            continue  # results will not match so don't run any of the packet test cases

        for packet_config, expected_outputs in packets:
            preamble_len, payload_len, explicit_header, crc_en = packet_config
            print(
                f" -- preamble_len={preamble_len} payload_len={payload_len} "
                + f"explicit_header={explicit_header} crc_en={crc_en}"
            )
            modem._preamble_len = preamble_len
            modem._implicit_header = not explicit_header  # opposite logic to calculator
            modem._crc_en = crc_en

            # Now calculate the symbol length and times and compare with the expected valuesd
            (
                expected_symbols,
                expected_symbol_time,
                expected_time_on_air,
            ) = expected_outputs

            print(f" ---- calculator shows total length {expected_symbols}")
            expected_symbols += 8  # Account for the calculator bug mentioned in the comment above

            n_symbols = modem.get_n_symbols_x4(payload_len) / 4.0
            symbol_time_us = modem._get_t_sym_us()
            time_on_air_us = modem.get_time_on_air_us(payload_len)

            tests += 1

            if n_symbols == expected_symbols:
                print(f" ---- symbols {n_symbols}")
            else:
                print(f" ---- SYMBOL COUNT ERROR expected {expected_symbols} got {n_symbols}")
                failures.add((modem, modem_settings, packet_config))

            max_error = expected_symbol_time * 1000 * TIME_ERROR_RATIO
            if abs(int(expected_symbol_time * 1000) - symbol_time_us) <= max_error:
                print(f" ---- symbol time {expected_symbol_time}ms")
            else:
                print(
                    f" ---- SYMBOL TIME ERROR expected {expected_symbol_time}ms "
                    + f"got {symbol_time_us}us"
                )
                failures.add((modem, modem_settings, packet_config))

            max_error = expected_time_on_air * 1000 * TIME_ERROR_RATIO
            if abs(int(expected_time_on_air * 1000) - time_on_air_us) <= max_error:
                print(f" ---- time on air {expected_time_on_air}ms")
            else:
                print(
                    f" ---- TIME ON AIR ERROR expected {expected_time_on_air}ms "
                    + f"got {time_on_air_us}us"
                )
                failures.add((modem, modem_settings, packet_config))

        print("************************")

    print(f"\n{len(failures)}/{tests} tests failed")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f)
        raise SystemExit(1)
    print("SUCCESS")


class DummySPI:
    # Dummy SPI Interface allows us to use normal constructors
    #
    # Reading will always return the 'always_read' value
    def __init__(self, always_read=0x00):
        self.always_read = always_read

    def write_readinto(self, _wrbuf, rdbuf):
        for i in range(len(rdbuf)):
            rdbuf[i] = self.always_read


class DummyPin:
    # Dummy Pin interface allows us to use normal constructors
    def __init__(self):
        pass

    def __call__(self, _=None):
        pass


# Copies of the functions used to calculate SX1276 SF5, SF6 test case symbol counts.
# (see comments above).
#
# These are written as closely to the SX1276 datasheet "Time on air" section as
# possible, quite different from the BaseModem implementation.


def sx1276_n_payload(pl, sf, ih, de, cr, crc):
    import math

    ceil_arg = 8 * pl - 4 * sf + 28 + 16 * crc - 20 * ih
    ceil_arg /= 4 * (sf - 2 * de)
    return 8 + max(math.ceil(ceil_arg) * (cr + 4), 0)


def sx1276_n_syms(pl, sf, ih, de, cr, crc, n_preamble):
    return sx1276_n_payload(pl, sf, ih, de, cr, crc) + n_preamble + 4.25


if __name__ == "__main__":
    main()
