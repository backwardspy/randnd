"""
Proxies requests to http://watchout4snakes.com/Random/RandomPhrase
"""

from dataclasses import dataclass, asdict
from enum import Enum, IntEnum
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import aiohttp


API_URL = "http://watchout4snakes.com/Random/RandomPhrase"


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


async def get_words(parts: list[PhrasePart]) -> list[str]:
    """
    Gets words from the API for the given phrase parts.
    """
    form_data = {}
    for i, part in enumerate(parts):
        form_data.update(
            {f"Pos{i+1}": part.pos.value, f"Level{i+1}": int(part.obscurity)}
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data=form_data) as response:
            body = await response.text()
            return body.split()


async def render_phrase(phrase: Phrase) -> tuple[str, list[str]]:
    """
    Renders the given phrase with words from the API.
    """
    words = await get_words(phrase.parts)
    cased_words = [
        word.title() if part.title else word
        for part, word in zip(phrase.parts, words)
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
app.add_middleware(CORSMiddleware, allow_origins=[
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://randnd.pigeon.life:5500",
], allow_methods="*", allow_headers="*")


async def make_response(phrase: Phrase) -> dict:
    """
    Makes a response for the given phrase.
    """
    result, words = await render_phrase(phrase)
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
