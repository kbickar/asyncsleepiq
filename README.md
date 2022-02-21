# AsyncSleepIQ

AsyncSleepIQ is an library for accessing the SleepIQ API from Python. [SleepIQ](http://www.sleepnumber.com/sn/en/sleepiq-sleep-tracker) is an addon for [SleepNumber beds](http://www.sleepnumber.com/).

## Installation

```bash
pip install asyncsleepiq
```

## Usage

The library is structured with classes `SleepIQBed`, `SleepIQSleeper`, and `SleepIQFoundation` that get updated with data fetched through the API.

After creating an intsance of `AsyncSleepIQ()` the `login` function should be called, followed by the `init_beds()` function to initialize the data structures and fetch the static data from the API.  Following that, the `fetch_bed_statuses()` function can be called to get updated bed occupancy and sleep number values.

There are two authentication methods available: The older API with key parameter and the newer cookie-based Authentication header.  As of Feb-2022 both work equally well.

The `login()` function should only be called once when the program is started, the `fetch_bed_statuses()` can be called more frequently to get the bed state.  When implementing, do not poll the API by calling `login` each time, instead keep the same `AsyncSleepIQ` object and fetch data as needed.  The library will re-authenticate automtically if the original authentication expires. 

Here is a full example

```python
import asyncio
from asyncsleepiq import AsyncSleepIQ, LOGIN_KEY, LOGIN_COOKIE

email = "user@example.com"
password = "passw0rd"

async def main():        
    api = AsyncSleepIQ(login_method=LOGIN_COOKIE)

    print(f"Logging in as {email}...")
    await api.login(email, password)

    print("Initializing bed data...")
    await api.init_beds()
    await api.fetch_bed_statuses()
    print("Beds:")
    for bed in api.beds.values(): 
        print(bed)

    bed = list(api.beds.values())[0]
    await bed.fetch_pause_mode()
    print (f"Pause mode: {bed.paused}")
    await bed.set_pause_mode(not bed.paused)   
    await bed.fetch_pause_mode()
    print (f"New Pause mode: {bed.paused}") 

    print("Calibrating...")
    await bed.calibrate()
    print("Stopping pump...")
    await bed.stop_pump()

asyncio.get_event_loop().run_until_complete(main())
```

## Future Development

Without documentation for the API, development requires obvserving how other interfaces interact with it.  Given the hardware dependencies are fairly high, any future development requires someone with the appropriate bed to be able to obvserve and test against.

## Special Thanks

Thanks to all the other people that have tried to dig into this API, especially the projects:

- https://github.com/technicalpickles/sleepyq (python)
- https://github.com/erichelgeson/sleepiq (swagger)
- https://github.com/DeeeeLAN/homebridge-sleepiq (javascript)
- https://bitbucket.org/Esity/sleepiq/ (ruby)
- https://javalibs.com/artifact/org.syphr/sleepiq-api (java)
