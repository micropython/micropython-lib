import jwt
import py_vapid
from time import time
from cryptography import ec
from machine import RTC


"""
Run tests by executing:

```
mpremote fs cp py_vapid/__init__.py :lib/py_vapid.py + run test_vapid.py
```

The [ucryptography](https://github.com/dmazzella/ucryptography) library must
be present in the firmware for this library and tests to work.
"""

rtc = RTC()

GOLDEN_0 = (
    0xEB6DFB26C7A3C23D33C60F7C7BA61B6893451F2643E0737B20759E457825EE75,
    (2010, 1, 1, 0, 0, 0, 0, 0),
    {
        "aud": "https://updates.push.services.mozilla.com",
        "sub": "mailto:admin@example.com",
        "exp": 9876543,
    },
    "vapid t=eyJ0eXAiOiAiSldUIiwgImFsZyI6ICJFUzI1NiJ9.eyJhdWQiOiAiaHR0cHM6Ly91cGRhdGVzLnB1c2guc2VydmljZXMubW96aWxsYS5jb20iLCAic3ViIjogIm1haWx0bzphZG1pbkBleGFtcGxlLmNvbSIsICJleHAiOiA5ODc2NTQzfQ.DLB6PF2RApzk0n0oH-Kv_Onuwg9C7VXakM-GlEMCwj50rQ7G0hF_vLIYzCPeXT8Hu8Uup900YBapZ9y45vc8QA,k=BKoKs6nJ3466nCEQ5TvFkBIGBKSGplPTUBzJlLXM13I8S0SF-o_NSB-Q4At3BeLSrZVptEd5xBuGRXCKMe_YRg8",
)

GOLDEN_1 = (
    0x4370082632776C74FDC5517AC12881413A60B25D10E863296AD67E4260A3BF56,
    (2015, 1, 1, 0, 0, 0, 0, 0),
    {
        "aud": "https://updates.push.services.mozilla.com",
        "sub": "mailto:admin@example.com",
    },
    "vapid t=eyJ0eXAiOiAiSldUIiwgImFsZyI6ICJFUzI1NiJ9.eyJleHAiOiAxNDIwMTU2ODAwLCAic3ViIjogIm1haWx0bzphZG1pbkBleGFtcGxlLmNvbSIsICJhdWQiOiAiaHR0cHM6Ly91cGRhdGVzLnB1c2guc2VydmljZXMubW96aWxsYS5jb20ifQ.NlVtqjGWy-hvNtoScrwAv-4cpNYrgUJ4EVgtxTnIn-haPtBSpak7aQN518tVYelQB1TZqc0bxAjWfK9QvZUbOA,k=BGEwf7m9F3vCvOuPeN4pEZ91t-dpSmg_y8ZXMfOyl-f22zw10ho_4EeBqZj2-NtW_Kb98b6tGjOKO_-TJiWvyfo",
)

# Set of opaquely known-good scenarios to check against
golden_test_cases = [GOLDEN_0, GOLDEN_1]


# Test basic validation of claim
private_key_0 = ec.derive_private_key(
    0x5C76C15BBC541E7BF6987557124A6E6EB745723B1CF20E2ED2A3ED5B7C16DD46, ec.SECP256R1()
)
vapid = py_vapid.Vapid(private_key=private_key_0)
rtc.datetime((2018, 1, 1, 0, 0, 0, 0, 0))
headers = vapid.sign(
    {
        "aud": "https://fcm.googleapis.com",
        "sub": "mailto:foo@bar.com",
        "exp": 1493315200,
    }
)

actual_token = headers["Authorization"].split(" ")[1].split(",")[0].split("=")[1]
actual_decoded_claim = jwt.decode(actual_token, private_key_0.public_key(), "ES256")
assert (
    actual_decoded_claim["aud"] == "https://fcm.googleapis.com"
), f"Claim audience '{actual_decoded_claim['aud']}' does not match input"
assert (
    actual_decoded_claim["sub"] == "mailto:foo@bar.com"
), f"Claim subscriber '{actual_decoded_claim['sub']}' does not match input"
assert (
    actual_decoded_claim["exp"] == 1493315200
), f"Claim exp '{actual_decoded_claim['exp']}' does not match input"
print(f"Test claim validation: Passed")


# Test auto expiration date population
private_key_1 = ec.derive_private_key(
    0x5C76C15BBC541E7BF6987557124A6E6EB745723B1CF20E2ED2A3ED5B7C16DD46, ec.SECP256R1()
)
vapid = py_vapid.Vapid(private_key=private_key_1)
rtc.datetime((2017, 1, 1, 0, 0, 0, 0, 0))
headers = vapid.sign(
    {
        "aud": "https://updates.push.services.mozilla.com",
        "sub": "mailto:admin@example.com",
    }
)

actual_token = headers["Authorization"].split(" ")[1].split(",")[0].split("=")[1]
actual_decoded_claim = jwt.decode(actual_token, private_key_1.public_key(), "ES256")
assert (
    actual_decoded_claim["exp"] == 1483315200
), f"Claim exp '{actual_decoded_claim['exp']}' does not match expected 2017-01-02 value"
print(f"Test auto expiry: Passed")


# Because they provide the least information about what could have gone wrong,
# Run golden test cases after all more specific tests pass first.
for case_no, case in enumerate(golden_test_cases):
    private_key_number, curr_time, claim, expected_id = case
    try:
        private_key = ec.derive_private_key(private_key_number, ec.SECP256R1())
        vapid = py_vapid.Vapid(private_key=private_key)
        rtc.datetime(curr_time)
        headers = vapid.sign(claim)

        assert (
            headers["Authorization"] == expected_id
        ), f"Authorization header '{headers['Authorization']}' does not match golden test case {case_no}"
        print(f"Golden test case {case_no}: Passed")
    except Exception as e:
        print(f"Golden test case {case_no}: Failed")
        raise e
