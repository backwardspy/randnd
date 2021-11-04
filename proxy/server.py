"""
API that renders phrases based on several wordlist sources.
"""

import random
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import Enum, IntEnum
from typing import Iterator, Protocol, TextIO
from pathlib import Path

import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class PartOfSpeech(Enum):
    """
    Maps parts of speech to the identifiers used on watchout4snakes.com
    """

    NOUN = "n"
    ADJECTIVE = "a"
    VERB_TRANSITIVE = "t"
    VERB_INTRANSITIVE = "i"
    ADVERB = "e"
    INTERJECTION = "z"
    PREPOSITION = "s"


class Obscurity(IntEnum):
    """
    Maps obscurities to the values used on watchout4snakes.com
    """

    VERY_COMMON = 10
    COMMON = 20
    AVERAGE = 35
    SOMEWHAT_UNCOMMON = 50
    UNCOMMON = 60
    VERY_UNCOMMON = 70
    OBSCURE = 95


@dataclass(frozen=True)
class PhrasePart:
    """
    Combines a POS (part of speech) and a obscurity level.
    """

    pos: PartOfSpeech
    obscurity: int
    title: bool = True


@dataclass(frozen=True)
class Phrase:
    """
    Combines a template and a list of parts of speech.
    """

    parts: list[PhrasePart]
    template: str

    def render(self, words: list[str]) -> str:
        """
        Renders the phrase using the given words from the API.
        """
        return self.template.format(*words)


class WordSource(Protocol):
    """
    A source of words for the API.
    """

    async def get_words(self, parts: list[PhrasePart]) -> list[str]:
        """
        Returns a list of words for the given parts of speech.
        """
        raise NotImplementedError


class Watchout4SnakesSource(WordSource):
    """
    Sources words from watchout4snakes.com
    """
    URL = "http://watchout4snakes.com/Random/RandomPhrase"

    async def get_words(self, parts: list[PhrasePart]) -> list[str]:
        """
        Gets words from the API for the given phrase parts.
        """
        form_data = {}
        for i, part in enumerate(parts):
            form_data.update(
                {f"Pos{i+1}": part.pos.value, f"Level{i+1}": int(part.obscurity)}
            )

        async with aiohttp.ClientSession() as session:
            async with session.post(self.URL, data=form_data) as response:
                body = await response.text()
                return body.split()


class VerachellSource(WordSource):
    """
    Sources words from the verachell-wordlists submodule.
    Ignores obscurity as we have no data for it.
    """
    BASE_PATH = Path("wordlists/verachell")
    FILES = {
        PartOfSpeech.NOUN: [
            BASE_PATH / "nouns" / "mostly-nouns-ment.txt",
            BASE_PATH / "nouns" / "mostly-nouns.txt",
            BASE_PATH / "nouns" / "mostly-plural-nouns.txt",
        ],
        PartOfSpeech.ADJECTIVE: [
            BASE_PATH / "other-categories" / "mostly-adjectives.txt",
        ],
        PartOfSpeech.VERB_TRANSITIVE: [
            BASE_PATH / "verbs" / "transitive-past-tense.txt",
            BASE_PATH / "verbs" / "transitive-present-tense.txt",
        ],
        PartOfSpeech.VERB_INTRANSITIVE: [
            BASE_PATH / "verbs" / "mostly-verbs-infinitive.txt",
            BASE_PATH / "verbs" / "mostly-verbs-past-tense.txt",
            BASE_PATH / "verbs" / "mostly-verbs-present-tense.txt",
        ],
        PartOfSpeech.ADVERB: [
            BASE_PATH / "other-categories" / "ly-adverbs.txt",
            BASE_PATH / "other-categories" / "mostly-adverbs.txt",
        ],
        PartOfSpeech.INTERJECTION: [
            BASE_PATH / "other-categories" / "mostly-interjections.txt",
        ],
        PartOfSpeech.PREPOSITION: [
            BASE_PATH / "other-categories" / "mostly-prepositions.txt",
        ],
    }

    def random_line(self, file: TextIO) -> str:
        """
        https://stackoverflow.com/a/3540315
        """
        chosen_line = next(file)
        for num, line in enumerate(file, 2):
            if random.randrange(num) != 0:
                continue
            chosen_line = line
        return chosen_line

    @contextmanager
    def random_file(self, pos: PartOfSpeech) -> Iterator[TextIO]:
        """
        Returns a random file from the given part of speech.
        """
        with random.choice(self.FILES[pos]).open("r") as file:
            yield file

    def get_word(self, part: PhrasePart) -> str:
        """
        Returns a word for the given phrase part.
        """
        with self.random_file(part.pos) as file:
            word = self.random_line(file).strip()
            if part.title:
                word = word.title()
            return word

    async def get_words(self, parts: list[PhrasePart]) -> list[str]:
        return [self.get_word(part) for part in parts]


async def render_phrase(phrase: Phrase, *, source: WordSource) -> tuple[str, list[str]]:
    """
    Renders the given phrase with words from the API.
    """
    words = await source.get_words(phrase.parts)
    cased_words = [
        word.title() if part.title else word for part, word in zip(phrase.parts, words)
    ]
    return phrase.render(cased_words), words


SPELL = Phrase(
    parts=[
        PhrasePart(pos=PartOfSpeech.VERB_TRANSITIVE, obscurity=Obscurity.AVERAGE),
        PhrasePart(pos=PartOfSpeech.NOUN, obscurity=Obscurity.AVERAGE),
    ],
    template="I cast {} {}.",
)

REACTION = Phrase(
    parts=[
        PhrasePart(pos=PartOfSpeech.INTERJECTION, obscurity=Obscurity.AVERAGE),
    ],
    template="{}!",
)

MINIBOSS = Phrase(
    parts=[
        PhrasePart(pos=PartOfSpeech.ADJECTIVE, obscurity=Obscurity.AVERAGE),
        PhrasePart(pos=PartOfSpeech.NOUN, obscurity=Obscurity.AVERAGE),
    ],
    template="You encounter the {} {}! What would you like to do?",
)

BOSS = Phrase(
    parts=[
        PhrasePart(pos=PartOfSpeech.ADJECTIVE, obscurity=Obscurity.AVERAGE),
        PhrasePart(pos=PartOfSpeech.ADJECTIVE, obscurity=Obscurity.AVERAGE),
        PhrasePart(pos=PartOfSpeech.NOUN, obscurity=Obscurity.AVERAGE),
    ],
    template="You've found the {} {} {}! What would you like to do?",
)

BBEG = Phrase(
    parts=[
        PhrasePart(pos=PartOfSpeech.ADJECTIVE, obscurity=Obscurity.AVERAGE),
        PhrasePart(pos=PartOfSpeech.NOUN, obscurity=Obscurity.AVERAGE),
        PhrasePart(
            pos=PartOfSpeech.PREPOSITION, obscurity=Obscurity.VERY_COMMON, title=False
        ),
        PhrasePart(pos=PartOfSpeech.NOUN, obscurity=Obscurity.AVERAGE),
    ],
    template="Finally, you've found the {} {} {} {}! What would you like to do?",
)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://randnd.pigeon.life:8000",
    ],
    allow_methods="*",
    allow_headers="*",
)

word_source = VerachellSource()


async def make_response(phrase: Phrase) -> dict:
    """
    Makes a response for the given phrase.
    """
    result, words = await render_phrase(phrase, source=word_source)
    return {"phrase": result, "words": words, "config": asdict(phrase)}


@app.get("/spell")
async def spell():
    """
    Returns a spell phrase.
    """
    return await make_response(SPELL)


@app.get("/reaction")
async def reaction():
    """
    Returns a reaction phrase.
    """
    return await make_response(REACTION)


@app.get("/miniboss")
async def miniboss():
    """
    Returns a miniboss phrase.
    """
    return await make_response(MINIBOSS)


@app.get("/boss")
async def boss():
    """
    Returns a boss phrase.
    """
    return await make_response(BOSS)


@app.get("/bbeg")
async def bbeg():
    """
    Returns a BBEG phrase.
    """
    return await make_response(BBEG)
