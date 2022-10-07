import utime

try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
host = "pool.ntp.org"


def time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]

    EPOCH_YEAR = utime.gmtime(0)[0]
    if EPOCH_YEAR == 2000:
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 3155673600
    elif EPOCH_YEAR == 1970:
        # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 2208988800
    else:
        raise Exception("Unsupported epoch: {}".format(EPOCH_YEAR))

    return val - NTP_DELTA


# There's currently no timezone support in MicroPython, and the RTC is set in UTC time.
def settime(tz: str = None):
    """
    function to get time from NTP server and set it to RTC
    :param tz : optional string parameter specifying the timezone 
    """
    t = time()
    tm = utime.gmtime(t)

    if tz:
        # list of all canonical timezones takes from wikipedia
        # https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        all_timezones = {
            "africa": {
                "abidjan": "+00:00",
                "algiers": "+01:00",
                "bissau": "+00:00",
                "cairo": "+02:00",
                "casablanca": "+01:00",
                "ceuta": "+01:00",
                "el_aaiun": "+01:00",
                "johannesburg": "+02:00",
                "juba": "+02:00",
                "khartoum": "+02:00",
                "lagos": "+01:00",
                "maputo": "+02:00",
                "monrovia": "+00:00",
                "nairobi": "+03:00",
                "ndjamena": "+01:00",
                "sao_tome": "+00:00",
                "tripoli": "+02:00",
                "tunis": "+01:00",
                "windhoek": "+02:00"
            },
            "america": {
                "adak": "−10:00",
                "anchorage": "−09:00",
                "araguaina": "−03:00",
                "argentina": {
                    "buenos_aires": "−03:00",
                    "catamarca": "−03:00",
                    "cordoba": "−03:00",
                    "jujuy": "−03:00",
                    "la_rioja": "−03:00",
                    "mendoza": "−03:00",
                    "rio_gallegos": "−03:00",
                    "salta": "−03:00",
                    "san_juan": "−03:00",
                    "san_luis": "−03:00",
                    "tucuman": "−03:00",
                    "ushuaia": "−03:00"
                },
                "asuncion": "−04:00",
                "bahia": "−03:00",
                "bahia_banderas": "−06:00",
                "barbados": "−04:00",
                "belem": "−03:00",
                "belize": "−06:00",
                "boa_vista": "−04:00",
                "bogota": "−05:00",
                "boise": "−07:00",
                "cambridge_bay": "−07:00",
                "campo_grande": "−04:00",
                "cancun": "−05:00",
                "caracas": "−04:00",
                "cayenne": "−03:00",
                "chicago": "−06:00",
                "chihuahua": "−07:00",
                "costa_rica": "−06:00",
                "cuiaba": "−04:00",
                "danmarkshavn": "+00:00",
                "dawson": "−07:00",
                "dawson_creek": "−07:00",
                "denver": "−07:00",
                "detroit": "−05:00",
                "edmonton": "−07:00",
                "eirunepe": "−05:00",
                "el_salvador": "−06:00",
                "fort_nelson": "−07:00",
                "fortaleza": "−03:00",
                "glace_bay": "−04:00",
                "goose_bay": "−04:00",
                "grand_turk": "−05:00",
                "guatemala": "−06:00",
                "guayaquil": "−05:00",
                "guyana": "−04:00",
                "halifax": "−04:00",
                "havana": "−05:00",
                "hermosillo": "−07:00",
                "indiana": {
                    "indianapolis": "−05:00",
                    "knox": "−06:00",
                    "marengo": "−05:00",
                    "petersburg": "−05:00",
                    "tell_city": "−06:00",
                    "vevay": "−05:00",
                    "vincennes": "−05:00",
                    "winamac": "−05:00"
                },
                "inuvik": "−07:00",
                "iqaluit": "−05:00",
                "jamaica": "−05:00",
                "juneau": "−09:00",
                "kentucky": {
                    "louisville": "−05:00",
                    "monticello": "−05:00"
                },
                "la_paz": "−04:00",
                "lima": "−05:00",
                "los_angeles": "−08:00",
                "maceio": "−03:00",
                "managua": "−06:00",
                "manaus": "−04:00",
                "martinique": "−04:00",
                "matamoros": "−06:00",
                "mazatlan": "−07:00",
                "menominee": "−06:00",
                "merida": "−06:00",
                "metlakatla": "−09:00",
                "mexico_city": "−06:00",
                "miquelon": "−03:00",
                "moncton": "−04:00",
                "monterrey": "−06:00",
                "montevideo": "−03:00",
                "new_york": "−05:00",
                "nipigon": "−05:00",
                "nome": "−09:00",
                "noronha": "−02:00",
                "north_dakota": {
                    "beulah": "−06:00",
                    "center": "−06:00",
                    "new_salem": "−06:00"
                },
                "nuuk": "−03:00",
                "ojinaga": "−07:00",
                "panama": "−05:00",
                "pangnirtung": "−05:00",
                "paramaribo": "−03:00",
                "phoenix": "−07:00",
                "port-au-prince": "−05:00",
                "porto_velho": "−04:00",
                "puerto_rico": "−04:00",
                "punta_arenas": "−03:00",
                "rainy_river": "−06:00",
                "rankin_inlet": "−06:00",
                "recife": "−03:00",
                "regina": "−06:00",
                "resolute": "−06:00",
                "rio_branco": "−05:00",
                "santarem": "−03:00",
                "santiago": "−04:00",
                "santo_domingo": "−04:00",
                "sao_paulo": "−03:00",
                "scoresbysund": "−01:00",
                "sitka": "−09:00",
                "st_johns": "−03:30",
                "swift_current": "−06:00",
                "tegucigalpa": "−06:00",
                "thule": "−04:00",
                "thunder_bay": "−05:00",
                "tijuana": "−08:00",
                "toronto": "−05:00",
                "vancouver": "−08:00",
                "whitehorse": "−07:00",
                "winnipeg": "−06:00",
                "yakutat": "−09:00",
                "yellowknife": "−07:00"
            },
            "antarctica": {
                "casey": "+11:00",
                "davis": "+07:00",
                "macquarie": "+10:00",
                "mawson": "+05:00",
                "palmer": "−03:00",
                "rothera": "−03:00",
                "troll": "+00:00"
            },
            "asia": {
                "almaty": "+06:00",
                "amman": "+02:00",
                "anadyr": "+12:00",
                "aqtau": "+05:00",
                "aqtobe": "+05:00",
                "ashgabat": "+05:00",
                "atyrau": "+05:00",
                "baghdad": "+03:00",
                "baku": "+04:00",
                "bangkok": "+07:00",
                "barnaul": "+07:00",
                "beirut": "+02:00",
                "bishkek": "+06:00",
                "chita": "+09:00",
                "choibalsan": "+08:00",
                "colombo": "+05:30",
                "damascus": "+02:00",
                "dhaka": "+06:00",
                "dili": "+09:00",
                "dubai": "+04:00",
                "dushanbe": "+05:00",
                "famagusta": "+02:00",
                "gaza": "+02:00",
                "hebron": "+02:00",
                "ho_chi_minh": "+07:00",
                "hong_kong": "+08:00",
                "hovd": "+07:00",
                "irkutsk": "+08:00",
                "jakarta": "+07:00",
                "jayapura": "+09:00",
                "jerusalem": "+02:00",
                "kabul": "+04:30",
                "kamchatka": "+12:00",
                "karachi": "+05:00",
                "kathmandu": "+05:45",
                "khandyga": "+09:00",
                "kolkata": "+05:30",
                "krasnoyarsk": "+07:00",
                "kuching": "+08:00",
                "macau": "+08:00",
                "magadan": "+11:00",
                "makassar": "+08:00",
                "manila": "+08:00",
                "nicosia": "+02:00",
                "novokuznetsk": "+07:00",
                "novosibirsk": "+07:00",
                "omsk": "+06:00",
                "oral": "+05:00",
                "pontianak": "+07:00",
                "pyongyang": "+09:00",
                "qatar": "+03:00",
                "qostanay": "+06:00",
                "qyzylorda": "+05:00",
                "riyadh": "+03:00",
                "sakhalin": "+11:00",
                "samarkand": "+05:00",
                "seoul": "+09:00",
                "shanghai": "+08:00",
                "singapore": "+08:00",
                "srednekolymsk": "+11:00",
                "taipei": "+08:00",
                "tashkent": "+05:00",
                "tbilisi": "+04:00",
                "tehran": "+03:30",
                "thimphu": "+06:00",
                "tokyo": "+09:00",
                "tomsk": "+07:00",
                "ulaanbaatar": "+08:00",
                "urumqi": "+06:00",
                "ust-nera": "+10:00",
                "vladivostok": "+10:00",
                "yakutsk": "+09:00",
                "yangon": "+06:30",
                "yekaterinburg": "+05:00",
                "yerevan": "+04:00"
            },
            "atlantic": {
                "azores": "−01:00",
                "bermuda": "−04:00",
                "canary": "+00:00",
                "cape_verde": "−01:00",
                "faroe": "+00:00",
                "madeira": "+00:00",
                "south_georgia": "−02:00",
                "stanley": "−03:00"
            },
            "australia": {
                "adelaide": "+09:30",
                "brisbane": "+10:00",
                "broken_hill": "+09:30",
                "darwin": "+09:30",
                "eucla": "+08:45",
                "hobart": "+10:00",
                "lindeman": "+10:00",
                "lord_howe": "+10:30",
                "melbourne": "+10:00",
                "perth": "+08:00",
                "sydney": "+10:00"
            },
            "cet": "+01:00",
            "cst6cdt": "-06:00",
            "eet": "+02:00",
            "est": "-05:00",
            "est5edt": "-05:00",
            "etc": {
                "gmt": "+00:00",
                "gmt+1": "−01:00",
                "gmt+10": "−10:00",
                "gmt+11": "−11:00",
                "gmt+12": "−12:00",
                "gmt+2": "−02:00",
                "gmt+3": "−03:00",
                "gmt+4": "−04:00",
                "gmt+5": "−05:00",
                "gmt+6": "−06:00",
                "gmt+7": "−07:00",
                "gmt+8": "−08:00",
                "gmt+9": "−09:00",
                "gmt-1": "+01:00",
                "gmt-10": "+10:00",
                "gmt-11": "+11:00",
                "gmt-12": "+12:00",
                "gmt-13": "+13:00",
                "gmt-14": "+14:00",
                "gmt-2": "+02:00",
                "gmt-3": "+03:00",
                "gmt-4": "+04:00",
                "gmt-5": "+05:00",
                "gmt-6": "+06:00",
                "gmt-7": "+07:00",
                "gmt-8": "+08:00",
                "gmt-9": "+09:00",
                "utc": "+00:00"
            },
            "europe": {
                "andorra": "+01:00",
                "astrakhan": "+04:00",
                "athens": "+02:00",
                "belgrade": "+01:00",
                "berlin": "+01:00",
                "brussels": "+01:00",
                "bucharest": "+02:00",
                "budapest": "+01:00",
                "chisinau": "+02:00",
                "dublin": "+01:00",
                "gibraltar": "+01:00",
                "helsinki": "+02:00",
                "istanbul": "+03:00",
                "kaliningrad": "+02:00",
                "kirov": "+03:00",
                "kyiv": "+02:00",
                "lisbon": "+00:00",
                "london": "+00:00",
                "madrid": "+01:00",
                "malta": "+01:00",
                "minsk": "+03:00",
                "moscow": "+03:00",
                "paris": "+01:00",
                "prague": "+01:00",
                "riga": "+02:00",
                "rome": "+01:00",
                "samara": "+04:00",
                "saratov": "+04:00",
                "simferopol": "+03:00",
                "sofia": "+02:00",
                "tallinn": "+02:00",
                "tirane": "+01:00",
                "ulyanovsk": "+04:00",
                "vienna": "+01:00",
                "vilnius": "+02:00",
                "volgograd": "+03:00",
                "warsaw": "+01:00",
                "zurich": "+01:00"
            },
            "factory": "+00:00",
            "hst": "-10:00",
            "indian": {
                "chagos": "+06:00",
                "maldives": "+05:00",
                "mauritius": "+04:00"
            },
            "met": "+01:00",
            "mst": "-07:00",
            "mst7mdt": "-07:00",
            "pacific": {
                "apia": "+13:00",
                "auckland": "+12:00",
                "bougainville": "+11:00",
                "chatham": "+12:45",
                "easter": "−06:00",
                "efate": "+11:00",
                "fakaofo": "+13:00",
                "fiji": "+12:00",
                "galapagos": "−06:00",
                "gambier": "−09:00",
                "guadalcanal": "+11:00",
                "guam": "+10:00",
                "honolulu": "−10:00",
                "kanton": "+13:00",
                "kiritimati": "+14:00",
                "kosrae": "+11:00",
                "kwajalein": "+12:00",
                "marquesas": "−09:30",
                "nauru": "+12:00",
                "niue": "−11:00",
                "norfolk": "+11:00",
                "noumea": "+11:00",
                "pago_pago": "−11:00",
                "palau": "+09:00",
                "pitcairn": "−08:00",
                "port_moresby": "+10:00",
                "rarotonga": "−10:00",
                "tahiti": "−10:00",
                "tarawa": "+12:00",
                "tongatapu": "+13:00"
            }
        }

        tokens = tz.lower().split('/')
        for token in tokens:
            if token not in all_timezones.keys():
                raise Exception(f'Invalid timezone: {tz}')
            all_timezones = all_timezones[token]

        if all_timezones != '+00:00':
            hour = int(all_timezones[1:3])
            minute = int(all_timezones[4:6])
            seconds_to_alter = (hour * 60 * 60) + (minute * 60) * (-1 if all_timezones[0] == '-' else 1)
            tm = utime.gmtime(t + seconds_to_alter)

    import machine
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
