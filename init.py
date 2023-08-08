import sqlite3 as sql
import json
from PIL import ImageFont

class Ranking:
    # TODO: Add __slots__()
    
    def __init__(self, config: dict) -> None:
        self.level_scaling              = config["SCALING"]
        self.img_width                  = config["IMG_WIDTH"]
        self.img_height                 = config["IMG_HEIGHT"]
        self.icon_width                 = config["ICON_WIDTH"]
        self.icon_height                = config["ICON_HEIGHT"]
        self.w_offset                   = config["W_OFFSET"]
        self.h_offset                   = config["H_OFFSET"]
        self.bg_round_rad               = config["BG_ROUND_RAD"]
        self.bar_round_rad              = config["BAR_ROUND_RAD"]
        self.icon_round_rad             = config["ICON_ROUND_RAD"]
        self.font_size_name             = config["FONT_LARGE"]
        self.font_size_text             = config["FONT_SMALLER"]
        self.font_name                  = ImageFont.truetype("data\Montserrat-Bold.ttf", self.font_size_name)
        self.font_text                  = ImageFont.truetype("data\Montserrat-Bold.ttf", self.font_size_text)
        self.default_bg_color           = config["DEFAULT_BG_COLOR"]
        self.default_full_bar_color     = config["DEFAULT_FULL_BAR_COLOR"]
        self.default_progress_bar_color = config["DEFAULT_PROGRESS_BAR_COLOR"]
        self.default_text_color         = config["DEFAULT_TEXT_COLOR"]


class Config:
    # TODO: Add __slots__()
    
    def __init__(self, config: dict) -> None:
        self.inv_link               = config["INVITATION_LINK"]
        self.token                  = config["TOKEN"]
        self.owner_id               = config["OWNER_ID"]
        
        self.prefix                 = config["COMMAND_PREFIX"]
        self.embed_color            = config["EMBED_COLOR"]
        
        self.allowed_channels       = config["ALLOWED_CHANNELS"]
        self.testing_channel        = config["TESTING_CHANNEL"]
        self.gear_channel           = config["GEAR_CHANNEL"]
        self.guild_bosses_channel   = config["GUILD_BOSSES_CHANNEL"]
        self.guild_quests_channel   = config["GUILD_QUESTS_CHANNEL"]
        
        self.ranking                = Ranking(config["RANKING"])
        
    @classmethod
    def from_json(cls):
        print("Loading Config!")
        
        try:
            with open("data\\config.json", 'r') as cfg:
                config = json.load(cfg)
        except Exception as e:
            print(e); exit(1)
            
        return cls(config)


class Database:
    __slots__ = ("connection", "cursor")
    
    def __init__(self) -> None:
        print("Initializing database connection!")
        
        try:
            self._connection = sql.connect("data\\tidebot.db")
            self._cursor     = self._connection.cursor()
        except Exception as e:
            print(e); exit(1)
        
        res = self._cursor.execute("SELECT name FROM sqlite_master")
        
        if not any("gear" in table for table in res):
            print("Gear table doesn't exist! Initializing new table.")
            self._cursor.execute(""" CREATE TABLE gear( user_id INTEGER PRIMARY KEY, ap INTEGER, aap INTEGER, dp INTEGER,
                                                       accuracy INTEGER, dr INTEGER, evasion INTEGER,
                                                       class TEXT, level REAL, gear_planner TEXT, gear_image INTEGER ) """)
        
        if not any("levels" in table for table in res):
            print("Levels table doesn't exist! Initializing new table.")
            self._cursor.execute(""" CREATE TABLE levels( user_id INTEGER PRIMARY KEY, exp INTEGER, level INTEGER, 
                                                         bg_color INTEGER, full_bar_color INTEGER, progress_bar_color INTEGER,
                                                         text_color INTEGER, bg_image INTEGER ) """)
    
    
    @property
    def connection(self):
        return self._connection
    
    @property
    def cursor(self):
        return self._cursor
    
    
    def execute(self, command: str):
        self._cursor.execute(command)
    
    
    def close(self):
        print("Closing database connection!")
        
        self._cursor.close()
        self._connection.close()     

        
cfg = Config.from_json()
db = Database()