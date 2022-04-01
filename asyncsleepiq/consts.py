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

FAVORITE = 1
READ = 2
WATCH_TV = 3
FLAT = 4
ZERO_G = 5
SNORE = 6

NO_PRESET = "Not at preset"

BED_PRESETS = {
    NO_PRESET: 0,
    "Favorite": FAVORITE,
    "Read": READ,
    "Watch TV": WATCH_TV,
    "Flat": FLAT,
    "Zero G": ZERO_G,
    "Snore": SNORE,
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
