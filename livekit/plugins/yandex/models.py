# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Literal

# Yandex SpeechKit supported models
YandexSTTModels = Literal[
    "general",
    "general:rc",
    "general:deprecated",
]

# Yandex SpeechKit supported languages
YandexSTTLanguages = Literal[
    "ru-RU",  # Russian
    "en-US",  # English (US)
    "tr-TR",  # Turkish
    "kk-KK",  # Kazakh
    "uz-UZ",  # Uzbek
    "hy-AM",  # Armenian
    "he-IL",  # Hebrew
    "ar",  # Arabic
    "eu",  # Basque
    "ba",  # Bashkir
    "be",  # Belarusian
    "bg",  # Bulgarian
    "ca",  # Catalan
    "cs",  # Czech
    "da",  # Danish
    "de",  # German
    "el",  # Greek
    "es",  # Spanish
    "et",  # Estonian
    "fi",  # Finnish
    "fr",  # French
    "ga",  # Irish
    "it",  # Italian
    "ja",  # Japanese
    "ko",  # Korean
    "ky",  # Kyrgyz
    "lt",  # Lithuanian
    "lv",  # Latvian
    "mn",  # Mongolian
    "nl",  # Dutch
    "no",  # Norwegian
    "pl",  # Polish
    "pt",  # Portuguese
    "ro",  # Romanian
    "sk",  # Slovak
    "sl",  # Slovenian
    "sv",  # Swedish
    "tg",  # Tajik
    "th",  # Thai
    "tt",  # Tatar
    "uk",  # Ukrainian
    "vi",  # Vietnamese
    "zh",  # Chinese
]

# Audio encoding formats supported by Yandex SpeechKit
YandexAudioEncoding = Literal["LINEAR16_PCM",]
