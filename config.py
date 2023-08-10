import json
from PIL import ImageFont

class _Ranking:
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
        self.path                       = config["BACKGROUND_FOLDER"]


class _Gear:
    #TODO: Add __slots__()
    
    def __init__(self, config: dict) -> None:
        self.browser_window_width       = config["BROWSER_WINDOW_WIDTH"]
        self.browser_window_height      = config["BROWSER_WINDOW_HEIGHT"]
        self.browser_exec_path          = config["BROWSER_EXEC_PATH"]
        self.img_x                      = config["IMG_X"]
        self.img_y                      = config["IMG_Y"]
        self.img_width                  = config["IMG_WIDTH"]
        self.img_height                 = config["IMG_HEIGHT"]
        self.extra_stats                = config["EXTRA_STATS"]
        self.path                       = config["IMG_FOLDER"]


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
        
        self.ranking                = _Ranking(config["RANKING"])
        self.gear                   = _Gear(config["GEAR"])
        
        
    @classmethod
    def from_json(cls):
        print("Loading Config!")
        
        try:
            with open("data\\config.json", 'r') as cfg:
                config = json.load(cfg)
        except Exception as e:
            print(e); exit(1)
            
        return cls(config)

cfg = Config.from_json()
