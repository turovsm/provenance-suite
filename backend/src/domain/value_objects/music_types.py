import enum


class MediaType(enum.StrEnum):
    CD = "CD"
    DVD = "DVD"
    BD = "BD"
    CASSETTE = "Cassette"
    VINYL = "Vinyl"
    WEB = "Web"


class ContainerFormat(enum.StrEnum):
    TRACKS = "Tracks"
    ISO = "ISO"
    MDF = "MDF"
    BIN_CUE = "BIN_CUE"
    CDI = "CDI"
    IMG = "IMG"
    VOB = "VOB"


class LogType(enum.StrEnum):
    EAC = "EAC"
    XLD = "XLD"
    EZCD = "EZCD"
    CUERIPPER = "CUERipper"
    CYANRIP = "cyanrip"
    WHIPPER = "whipper"


class AudioCodec(enum.StrEnum):
    FLAC = "FLAC"
    MP3 = "MP3"
    ALAC = "ALAC"
    AAC = "AAC"
    PCM = "PCM"
    AC3 = "AC3"
    DTS = "DTS"
    WMA = "WMA"
    WAVPACK = "WavPack"


class VideoCodec(enum.StrEnum):
    MPEG2 = "MPEG2"
    H264 = "H264"
    HEVC = "HEVC"
    VC1 = "VC1"


class BitrateMode(enum.StrEnum):
    CBR = "CBR"
    VBR = "VBR"
    ABR = "ABR"
