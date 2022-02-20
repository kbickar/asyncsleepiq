class SleepIQLight:
    def __init__(self, api, bed_id, outlet_id):
        self._api = api
        self.bed_id = bed_id
        self.is_on = False
        self.outlet_id = outlet_id

    def __str__(self):
        return f"SleepIQLight[{self.outlet_id}]: {'On' if self.is_on else 'Off'}"
    def __repr__(self):
        return f"SleepIQLight[{self.outlet_id}]: {'On' if self.is_on else 'Off'}"

    async def turn_on(self):
        await self.set_light(True)
        self.is_on = True

    async def turn_off(self):
        await self.set_light(False)
        self.is_on = False

    async def set_light(self, on):
        data = {"outletId": self.outlet_id, "setting": 1 if on else 0}
        await self._api.put(f"bed/{self.bed_id}/foundation/outlet", data)

    async def update(self):
        params = {"outletId": self.outlet_id}
        status = await self._api.get(f"bed/{self.bed_id}/foundation/outlet", params=params)
        self.is_on = status["setting"] == 1