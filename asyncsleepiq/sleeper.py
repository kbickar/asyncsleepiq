from .consts import *
        
class SleepIQSleeper:
    def __init__(self, api, bed_id, sleeper_id, side):
        self.api = api
        self.bed_id = bed_id
        self.sleeper_id = sleeper_id
        self.side = SIDES[side]
        self.side_full = SIDES_FULL[side]
        self.active = False
        self.name = ""
        
        self.in_bed = False
        self.pressure = 0
        self.sleep_number = 0
        self.fav_sleep_number = 0
        
        
    def __str__(self):
        return f"SleepIQSleeper[{self.side}]({self.name}, in_bed={self.in_bed}, sn={self.sleep_number})" 
    def __repr__(self):
        return f"SleepIQSleeper[{self.side}]({self.name}, in_bed={self.in_bed}, sn={self.sleep_number})" 

    # Calibrate or "baseline" bed
    async def calibrate(self):
        await self.api.put('sleeper/'+self.sleeper_id+'/calibrate')

    # Set sleep number 5-100 (multiple of 5)
    #  Note: This function does not work on all models, even if sleep number can be fetched
    async def set_sleepnumber(self, setting):
        if 0 > setting or setting > 100 :
            raise ValueError("Invalid SleepNumber, must be between 0 and 100")
        setting = int(round(setting/5))*5
        data = {"sleepNumber": setting, 'side': self.side}
        await self.api.put('bed/'+self.bed_id+'/sleepNumber', data)


    # Set favorite sleep number 5-100 (multiple of 5)
    async def set_favsleepnumber(self, setting):
        if 0 > setting or setting > 100:
            raise ValueError("Invalid SleepNumber, must be between 0 and 100")
        setting = int(round(setting/5))*5
        data = {'side': self.side, "sleepNumberFavorite": setting}
        await self.api.put('bed/'+self.bed_id+'/sleepNumberFavorite', data)
        await self.update_favsleepnumber()


    async def fetch_favsleepnumber(self):
        json = await self.api.get('bed/'+self.bed_id+'/sleepNumberFavorite')
        self.fav_sleep_number = json['sleepNumberFavorite'+ self.side_full]


