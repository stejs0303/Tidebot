import re


class _Regex:
    # TODO: Add __slots__()
    def __init__(self) -> None:
        self.hexa_hash          = re.compile(r"^#[0-9a-f]{6}$")
        self.hexa_0x            = re.compile(r"^0x[0-9a-f]{6}$")
        self.int_pattern        = re.compile(r"^\d+$")
        self.percentage         = re.compile(r"^\d+((\.|,)\d+)?\ ?%?$")
        self.garmoth_url        = re.compile(r"^(https:\/\/|http:\/\/|www.)garmoth.com\/character\/[0-9a-zA-Z]{10}$")
        self.emote              = re.compile(r"^<:[a-zA-Z0-9]+:\d+>$")
        self.tripplet           = re.compile(r"^(\( ?\d+, ?\d+, ?\d+ ?\))$")
        self.string_or_level    = re.compile(r"(^[a-zA-z]+$)|(^\d+(.|,)\d+$)")



regex = _Regex()