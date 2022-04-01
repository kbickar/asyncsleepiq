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

OFF = 0
LOW = 1
MEDIUM = 2
HIGH = 3

MASSAGE_SPEED = [OFF, LOW, MEDIUM, HIGH]

SOOTHE = 1
REVITILIZE = 2
WAVE = 3

MASSAGE_MODE = [OFF, SOOTHE, REVITILIZE, WAVE]

class Side(str, enum.Enum):
    LEFT = "L"
    RIGHT = "R"
    NONE = "R"
SIDES_FULL = {Side.LEFT: "Left", Side.RIGHT: "Right"}

FOUNDATION_TYPES = ["single", "splitHead", "splitKing", "easternKing"]

class End(str, enum.Enum):
    HEAD = "H"
    FOOT = "F"
ACTUATORS_FULL = {End.HEAD: "Head", End.FOOT: "Foot"}
