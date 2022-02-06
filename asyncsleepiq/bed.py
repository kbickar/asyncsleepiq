from .sleeper import *
from .foundation import *
from .consts import *

class SleepIQBed:
    def __init__(self, api, data):
        self._api = api
        
        self.name = data['name']
        self.id = data['bedId']
        self.mac_addr = data['macAddress']
        self.paused = False
        self.sleepers = [
            SleepIQSleeper(api, self.id, data['sleeperLeftId'], 0),
            SleepIQSleeper(api, self.id, data['sleeperRightId'], 1),
        ]
        self.foundation = SleepIQFoundation(api, self.id)
        
        self.model = "Unknown"
        if 'model' in data:
            self.model = data['model']
        elif 'components' in data:
            for comp in data['components']:
                if comp['base'] == "BASE":
                    self.model = comp['model']
                    break
       
    def __str__(self):
        return f"SleepIQBed({self.name}, model={self.model}, id={self.id}) "+str(self.sleepers)+" "+str(self.foundation)
    def __repr__(self):
        return f"SleepIQBed({self.name}, model={self.model}, id={self.id}) "+str(self.sleepers)+" "+str(self.foundation)
        
    # Calibrate or "baseline" bed
    async def calibrate(self):
        for sleeper in self.sleepers:
            if sleeper.sleeper_id:
                await sleeper.calibrate()
                break
        
    async def stop_pump(self):
        await self._api.put('bed/'+self.id+'/pump/forceIdle')
        
    async def fetch_pause_mode(self):
        json = await self._api.get('bed/'+self.id+'/pauseMode')
        self.paused = json.get('pauseMode',"") == "on"
        
    async def set_pause_mode(self, mode):
        params = {'mode': "on" if mode else "off"}
        await self._api.put('bed/'+self.id+'/pauseMode', params=params)
        self.paused = mode
        