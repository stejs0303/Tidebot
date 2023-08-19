import json
from PIL import ImageFont

class _Ranking:
    # TODO: Add __slots__()
    
    def __init__(self, ranking: dict) -> None:
        self.level_scaling              = ranking["SCALING"]
        self.img_width                  = ranking["IMG_WIDTH"]
        self.img_height                 = ranking["IMG_HEIGHT"]
        self.icon_width                 = ranking["ICON_WIDTH"]
        self.icon_height                = ranking["ICON_HEIGHT"]
        self.w_offset                   = ranking["W_OFFSET"]
        self.h_offset                   = ranking["H_OFFSET"]
        self.bg_round_rad               = ranking["BG_ROUND_RAD"]
        self.bar_round_rad              = ranking["BAR_ROUND_RAD"]
        self.icon_round_rad             = ranking["ICON_ROUND_RAD"]
        self.font_size_name             = ranking["FONT_LARGE"]
        self.font_size_text             = ranking["FONT_SMALLER"]
        self.font_name                  = ImageFont.truetype("data\Montserrat-Bold.ttf", self.font_size_name)
        self.font_text                  = ImageFont.truetype("data\Montserrat-Bold.ttf", self.font_size_text)
        self.default_bg_color           = ranking["DEFAULT_BG_COLOR"]
        self.default_full_bar_color     = ranking["DEFAULT_FULL_BAR_COLOR"]
        self.default_progress_bar_color = ranking["DEFAULT_PROGRESS_BAR_COLOR"]
        self.default_text_color         = ranking["DEFAULT_TEXT_COLOR"]
        self.path                       = ranking["BACKGROUND_FOLDER"]


class _Gear:
    #TODO: Add __slots__()
    
    def __init__(self, gear: dict) -> None:
        self.browser_window_width       = gear["BROWSER_WINDOW_WIDTH"]
        self.browser_window_height      = gear["BROWSER_WINDOW_HEIGHT"]
        self.webdriver_path             = gear["WEBDRIVER_PATH"]
        self.img_x                      = gear["IMG_X"]
        self.img_y                      = gear["IMG_Y"]
        self.img_width                  = gear["IMG_WIDTH"]
        self.img_height                 = gear["IMG_HEIGHT"]
        self.include                    = gear["INCLUDE_STATS"]
        self.exclude                    = gear["EXCLUDE_STATS"]
        self.path                       = gear["IMG_FOLDER"]


class _Config:
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



cfg = _Config.from_json()