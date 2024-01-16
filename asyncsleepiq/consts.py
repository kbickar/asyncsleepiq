"""Constants for SleepIQ API Package."""
import enum

API_URL = "https://prod-api.sleepiq.sleepnumber.com/rest"
TIMEOUT = 10

LOGIN_KEY = 1
LOGIN_COOKIE = 2

RIGHT_NIGHT_STAND = 1
LEFT_NIGHT_STAND = 2
RIGHT_NIGHT_LIGHT = 3
LEFT_NIGHT_LIGHT = 4

BED_LIGHTS = [RIGHT_NIGHT_STAND, LEFT_NIGHT_STAND, RIGHT_NIGHT_LIGHT, LEFT_NIGHT_LIGHT]


class FootWarmingTemps(int, enum.Enum):
    OFF = 0
    LOW = 31
    MEDIUM = 57
    HIGH = 72

class CoreTemps(int, enum.Enum):
    OFF = 0
    HEATING_PUSH_LOW = 21
    HEATING_PUSH_MED = 22
    HEATING_PUSH_HIGH = 23
    COOLING_PULL_LOW = 41
    COOLING_PULL_MED = 42
    COOLING_PULL_HIGH = 43

FAVORITE = 1
READ = 2
WATCH_TV = 3
FLAT = 4
ZERO_G = 5
SNORE = 6

NO_PRESET = "Not at preset"
PRESET_FAV = "Favorite"
PRESET_READ = "Read"
PRESET_TV = "Watch TV"
PRESET_FLAT = "Flat"
PRESET_ZERO_G = "Zero G"
PRESET_SNORE = "Snore"

BED_PRESETS = {
    NO_PRESET: 0,
    PRESET_FAV: FAVORITE,
    PRESET_READ: READ,
    PRESET_TV: WATCH_TV,
    PRESET_FLAT: FLAT,
    PRESET_ZERO_G: ZERO_G,
    PRESET_SNORE: SNORE,
}


class Speed(int, enum.Enum):
    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


MASSAGE_SPEEDS = [Speed.OFF, Speed.LOW, Speed.MEDIUM, Speed.HIGH]


class Mode(int, enum.Enum):
    OFF = 0
    SOOTHE = 1
    REVITILIZE = 2
    WAVE = 3


MASSAGE_MODES = [Mode.OFF, Mode.SOOTHE, Mode.REVITILIZE, Mode.WAVE]


class Side(str, enum.Enum):
    LEFT = "L"
    RIGHT = "R"
    NONE = "-"


SIDES_SHORT = {Side.LEFT: "L", Side.RIGHT: "R", Side.NONE: "R"}
SIDES_FULL = {Side.LEFT: "Left", Side.RIGHT: "Right", Side.NONE: "Right"}

FOUNDATION_TYPES = ["single", "splitHead", "splitKing", "easternKing"]


class End(str, enum.Enum):
    HEAD = "H"
    FOOT = "F"


ACTUATORS_FULL = {End.HEAD: "Head", End.FOOT: "Foot"}

BAMKEY = {
    "HaltAllActuators": "ACHA",
    "GetSystemConfiguration": "SYCG",
    "SetSleepiqPrivacyState": "SPRS",
    "GetSleepiqPrivacyState": "SPRG",
    "InterruptSleepNumberAdjustment": "PSNI",
    "StartSleepNumberAdjustment": "PSNS",
    "GetSleepNumberControls": "SNCG",
    "SetFavoriteSleepNumber": "SNFS",
    "GetFavoriteSleepNumber": "SNFG",
    "SetUnderbedLightSettings": "UBLS",
    "GetUnderbedLightSettings": "UBLG",
    "GetActuatorPosition": "ACTG",
    "SetActuatorTargetPosition": "ACTS",
    "SetTargetPresetWithoutTimer": "ASTP",
    "GetCurrentPreset": "AGCP",
    "GetFootwarmingPresence": "FWPG",
    "SetFootwarmingSettings": "FWTS",
    "GetFootwarmingSettings": "FWTG",
    "GetHeidiPresence": "THPG",
    "SetHeidiMode": "THMS",
    "GetHeidiMode": "THMG",
}
