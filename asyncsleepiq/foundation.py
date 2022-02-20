from .consts import BED_LIGHTS, BED_PRESETS, FOUNDATION_TYPES, MASSAGE_MODE, MASSAGE_SPEED
from .actuator import SleepIQActuator
from .light import SleepIQLight

class SleepIQFoundation:
    def __init__(self, api, bed_id):
        self._api = api
        self.bed_id = bed_id
        self.lights = []
        self.features = {}
        self.type = None
        self.actuators = []
        self.isMoving = False
        self.preset = ""
        
    def __str__(self):
        return f"SleepIQFoundation[{self.type}](lights: {len(self.lights)}, features: {len(self.features)}, actuators: {len(self.actuators)})" 
    def __repr__(self):
        return f"SleepIQFoundation[{self.type}](lights: {len(self.lights)}, features: {len(self.features)}, actuators: {len(self.actuators)})" 
        
    async def init_lights(self):
        for light in BED_LIGHTS:
            exists = await self._api.check(f"bed/{self.bed_id}/foundation/outlet", params={"outletId": light})
            if exists:
                self.lights.append(SleepIQLight(self._api, self.bed_id, light))
        await self.update_lights()

    async def update_lights(self):
        for light in self.lights:
            await light.update()

    async def init_actuators(self):
        if not self.type:
            return
        data = await self._api.get(f"bed/{self.bed_id}/foundation/status")
        self.isMoving = data["fsIsMoving"]

        if self.type in ["single", "easternKing"]:
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, None, 0),
                SleepIQActuator(self._api, self.bed_id, None, 1)
            ]
        elif self.type == "splitHead":
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, 0, 0),
                SleepIQActuator(self._api, self.bed_id, 1, 0),
                SleepIQActuator(self._api, self.bed_id, None, 1)
            ]
        else:
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, 0, 0),
                SleepIQActuator(self._api, self.bed_id, 1, 0),
                SleepIQActuator(self._api, self.bed_id, 0, 1),
                SleepIQActuator(self._api, self.bed_id, 1, 1)
            ]

        for actuator in self.actuators:
            await actuator.update(data)

    async def update_actuators(self):
        if not self.type:
            return
        data = await self._api.get(f"bed/{self.bed_id}/foundation/status")
        self.isMoving = data["fsIsMoving"]
        for actuator in self.actuators:
            await actuator.update(data)

    async def fetch_features(self):
        have_foundation = await self._api.check('bed/'+self.bed_id+'/foundation/system')
        if not have_foundation:
           self.type = None
           return           
                
        fs = await self._api.get('bed/'+self.bed_id+'/foundation/system')
        features_flags = fs.get('fsBoardFeatures')
        self.features['boardIsASingle'] = features_flags & (1 < 0)
        self.features['hasMassageAndLight'] = features_flags & (1 < 1)
        self.features['hasFootControl'] = features_flags & (1 < 2)
        self.features['hasFootWarming'] = features_flags & (1 < 3)
        self.features['hasUnderbedLight'] = features_flags & (1 < 4)
        self.type = FOUNDATION_TYPES[fs.get('fsBedType')]
        
        self.features['leftUnderbedLightPMW'] = fs.get('fsLeftUnderbedLightPWM')
        self.features['rightUnderbedLightPMW'] = fs.get('fsRightUnderbedLightPWM')

        if 'hasMassageAndLight' in self.features:
            self.features['hasUnderbedLight'] = True
        if 'split' in self.type:
            self.features['boardIsASingle'] = False
            
        
    async def stop_motion(self, side):
        data = {"footMotion":1, "headMotion":1, "massageMotion":1, "side":side}
        await self._api.put('bed/'+self.bed_id+'/foundation/motion', data)

    async def set_preset(self, side, preset, slowSpeed=False):
        #
        # preset 1-6
        # slowSpeed False=fast, True=slow
        #
        if preset not in BED_PRESETS:
            raise ValueError("Invalid preset")
            
        data = {'preset':preset,'side':side,'speed':1 if slowSpeed else 0}
        await self._api.put('bed/'+self.bed_id+'/foundation/preset', data)

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
        await self._api.put('bed/'+self.bed_id+'/foundation/adjustment', data)
