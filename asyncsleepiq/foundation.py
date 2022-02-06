from .sleeper import *
from .consts import *

class SleepIQFoundation:
    def __init__(self, api, bed_id):
        self._api = api
        self.bed_id = bed_id
        self.lights = {}
        self.features = {}
        self.type = None
        
    def __str__(self):
        return f"SleepIQFoundation[{self.type}](lights: {len(self.lights)}, features: {len(self.features)})" 
    def __repr__(self):
        return f"SleepIQFoundation[{self.type}](lights: {len(self.lights)}, features: {len(self.features)})" 
        
    async def init_lights(self):
        for light in BED_LIGHTS:
            params = {'outletId': light}
            exists = await self._api.check('bed/'+self.bed_id+'/foundation/outlet', params=params)
            if exists:
                get_light(self, light)
        
    # fetch states for all lights
    async def fetch_lights(self):
        for light in lights:
            await get_light(self, light)

    # Set light 1-4 on/off
    async def set_light(self, light, on):
        if light not in BED_LIGHTS:
            raise ValueError("Invalid light")
            
        data = {'outletId': light, 'setting': 1 if on else 0}
        await self._api.put('bed/'+self.bed_id+'/foundation/outlet', data)

    # fetch state for light
    async def fetch_light(self, light):
        if light not in BED_LIGHTS:
            raise ValueError("Invalid light")
        params = {'outletId': light}
        status = await self._api.get('bed/'+self.bed_id+'/foundation/outlet', params=params)
        self.lights[light] = status

    async def foundation_status(self):
        return await self._api.get('bed/'+self.bed_id+'/foundation/status')

    async def fetch_features(self):
        have_foundation = await self._api.check('bed/'+self.bed_id+'/foundation/system')
        if not have_foundation:
           self.type = None
           return           
                
        fs = await self._api.get('bed/'+self.bed_id+'/foundation/system')
        features_flags = getattr(fs, 'fsBoardFeatures')
        self.features['boardIsASingle'] = features_flags & (1 < 0)
        self.features['hasMassageAndLight'] = features_flags & (1 < 1)
        self.features['hasFootControl'] = features_flags & (1 < 2)
        self.features['hasFootWarming'] = features_flags & (1 < 3)
        self.features['hasUnderbedLight'] = features_flags & (1 < 4)
        self.type = FOUNDATION_TYPES[getattr(fs, 'fsBedType')]
        
        self.features['leftUnderbedLightPMW'] = getattr(fs, 'fsLeftUnderbedLightPWM')
        self.features['rightUnderbedLightPMW'] = getattr(fs, 'fsRightUnderbedLightPWM')

        if self.features['hasMassageAndLight']:
            self.features['hasUnderbedLight'] = True
        if self.features['splitKing'] or features['splitHead']:
            self.features['boardIsASingle'] = False
            
        
    async def stop_motion(self, side):
        data = {"footMotion":1, "headMotion":1, "massageMotion":1, "side":side}
        await api.put('bed/'+self.bed_id+'/foundation/motion', data)

    async def set_preset(self, side, preset, slowSpeed=False):
        #
        # preset 1-6
        # slowSpeed False=fast, True=slow
        #
        if preset not in BED_PRESETS:
            raise ValueError("Invalid preset")
            
        data = {'preset':preset,'side':side,'speed':1 if slowSpeed else 0}
        await api.put('bed/'+self.bed_id+'/foundation/preset', data)

    async def set_foundation_massage(self, side, footSpeed, headSpeed, timer=0, mode=0):
        #
        # footSpeed 0-3
        # headSpeed 0-3
        # mode 0-3
        #
        if mode not in MASSAGE_MODE:
            raise ValueError("Invalid mode")
        if mode != 0:
            footSpeed = 0
            headSpeed = 0
        if not all(speed in MASSAGE_SPEED for speed in [footSpeed, headSpeed]):
            raise ValueError("Invalid head or foot speed")
        
        data = {'footMassageMotor':footSpeed,
                'headMassageMotor':headSpeed,
                'massageTimer':timer,
                'massageWaveMode':mode,
                'side':side}
        await api.put('bed/'+self.bed_id+'/foundation/adjustment', data)


    async def set_foundation_position(self, side, actuator, position, slowSpeed=False):
        #
        # actuator "H" or "F" (head or foot)
        # position 0-100
        # slowSpeed False=fast, True=slow
        #
        if 0 > position or position > 100:
            raise ValueError("Invalid position, must be between 0 and 100")
        if actuator.lower() in ('h', 'head'):
            actuator = 'H'
        elif actuator.lower() in ('f', 'foot'):
            actuator = 'F'
        else:
            raise ValueError("Actuator must be one of the following: head, foot, H or F")
        data = {'position':position,'side':side,'actuator':actuator,'speed':1 if slowSpeed else 0}
        await api.put('bed/'+self.bed_id+'/foundation/adjustment/micro', data)
        