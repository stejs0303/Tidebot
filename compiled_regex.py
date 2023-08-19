import re


class _Regex:
    # TODO: Add __slots__()
    def __init__(self) -> None:
        self.hexa_hash          = re.compile(r"^#[0-9a-f]{6}$", flags=re.RegexFlag.MULTILINE)
        self.hexa_0x            = re.compile(r"^0x[0-9a-f]{6}$", flags=re.RegexFlag.MULTILINE)
        self.int_pattern        = re.compile(r"^\d+$", flags=re.RegexFlag.MULTILINE)
        self.percentage         = re.compile(r"^\d+((\.|,)\d+)?\ ?%?$", flags=re.RegexFlag.MULTILINE)
        self.garmoth_url        = re.compile(r"^(https:\/\/|http:\/\/|www.)garmoth.com\/character\/[0-9a-zA-Z]{10}$", 
                                             flags=re.RegexFlag.MULTILINE)


regex = _Regex()