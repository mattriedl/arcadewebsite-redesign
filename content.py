"""Page copy for search engines and visitors: titles, descriptions, intros, how-to-play text and FAQs.

Games with a hand-written entry in data/descriptions.json use it. Every other game gets copy built
from facts we actually know about it (its name, category, series and similar games), with the
wording varied by category so pages don't read as copies of each other.
"""
import hashlib
import re

def pick(options, key):
    """Choose one option, always the same one for the same key."""
    return options[int(hashlib.md5(key.encode()).hexdigest(), 16) % len(options)]

def clip(text, n):
    """Shorten to n characters at a word boundary."""
    if len(text) <= n:
        return text
    cut = text[: n - 1].rsplit(" ", 1)[0].rstrip(",;:–-")
    return cut + "…"

def first_sentence(text):
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return m.group(1) if m else text

# Lower-case category words used in sentences
NOUN = {
    "arcade": "arcade", "platformer": "platformer", "battle": "battle", "shooting": "shooting",
    "racing": "racing", "casual": "casual", "strategy": "strategy", "sports": "sports",
    "puzzle": "puzzle", "idle-clicker": "idle clicker", "horror": "horror", "minecraft": "Minecraft-style",
}

# What each kind of game is about, in a few different wordings
ABOUT = {
    "arcade": ["{t} is an arcade game built for quick sessions and one-more-try runs.",
               "{t} is a pick-up-and-play arcade game that's easy to start and hard to put down.",
               "{t} is a fast arcade game where every attempt is a chance to do a little better."],
    "platformer": ["{t} is a platform game about running, jumping and timing your moves.",
                   "{t} is a platformer where careful jumps and quick reactions get you to the end of each level.",
                   "{t} is a platform game full of gaps, traps and jumps to master."],
    "battle": ["{t} is a battle game where you take on opponents in quick, action-packed rounds.",
               "{t} is a fighting and battle game built around fast matches.",
               "{t} is a head-to-head battle game where quick reactions decide each round."],
    "shooting": ["{t} is a shooting game that tests your aim and reflexes.",
                 "{t} is an action shooting game where accuracy and timing win the fight.",
                 "{t} is a shooting game packed with enemies, targets and fast action."],
    "racing": ["{t} is a racing game about speed, control and finding the fastest line.",
               "{t} is a driving game where you race against the track, the clock or other drivers.",
               "{t} is a racing game that rewards clean driving and well-timed boosts."],
    "casual": ["{t} is a relaxed casual game that's easy to learn and perfect for a short break.",
               "{t} is a casual game with simple rules and satisfying, bite-sized rounds.",
               "{t} is a light casual game you can enjoy in a few minutes at a time."],
    "strategy": ["{t} is a strategy game where planning ahead is the key to winning.",
                 "{t} is a strategy game about smart decisions, resources and timing.",
                 "{t} is a strategy game that rewards thinking a few moves ahead."],
    "sports": ["{t} is a sports game you can play right in your browser.",
               "{t} is a sports game built for quick matches and friendly competition.",
               "{t} is an arcade-style sports game with fast, easy-to-learn gameplay."],
    "puzzle": ["{t} is a puzzle game that gets you thinking.",
               "{t} is a brain-teasing puzzle game with challenges that start easy and get tricky.",
               "{t} is a logic and puzzle game for players who like a good challenge."],
    "idle-clicker": ["{t} is an idle clicker game: earn, upgrade and watch your progress grow.",
                     "{t} is a clicker game where every upgrade helps you earn faster.",
                     "{t} is an idle game that keeps rewarding you as your upgrades stack up."],
    "horror": ["{t} is a horror game with tense moments and scares around every corner.",
               "{t} is a spooky horror game best played with the lights off.",
               "{t} is a horror game about surviving, exploring and keeping your nerve."],
    "minecraft": ["{t} is a block-building game in the style of Minecraft.",
                  "{t} lets you mine, craft and build in a blocky world right in your browser.",
                  "{t} is a Minecraft-style sandbox for building and exploring."],
}

# General play advice per category. It never claims specific controls we haven't checked.
HOWTO = {
    "arcade": "Click Play to start, then follow the on-screen instructions. Most arcade games use the arrow keys, WASD, the space bar or the mouse, and the game shows its controls when it begins.",
    "platformer": "Click Play to start. Platform games usually use the arrow keys or WASD to move and the up arrow, W or the space bar to jump. Take your time on tricky jumps and learn each level's pattern.",
    "battle": "Click Play to start. Battle games usually use WASD or the arrow keys to move and a few keys to attack. Many support two players on one keyboard, with the controls shown before the match.",
    "shooting": "Click Play to start. Most shooting games use WASD or the arrow keys to move and the mouse to aim and shoot. Check the game's menu for its exact controls.",
    "racing": "Click Play to start. Racing games usually use the arrow keys or WASD to drive, with the space bar for the brake or boost. The game shows its controls before the first race.",
    "casual": "Click Play to start. Casual games are usually played with the mouse or a single key, so you can jump straight in.",
    "strategy": "Click Play to start. Strategy games are usually played with the mouse: select units or towers and click to place or command them. Read the tutorial if the game has one.",
    "sports": "Click Play to start. Sports games usually use the arrow keys or WASD to move, with one or two keys to pass, shoot or jump. Many let two players share one keyboard.",
    "puzzle": "Click Play to start. Puzzle games are usually played with the mouse or the arrow keys. There's no rush, so think before each move.",
    "idle-clicker": "Click Play to start. Click to earn your first resources, then spend them on upgrades that earn for you. Progress is usually saved in your browser.",
    "horror": "Click Play to start. Horror games usually use WASD to move and the mouse to look around. Fullscreen and headphones make them much scarier.",
    "minecraft": "Click Play to start. Move with WASD, look around with the mouse, left-click to break blocks and right-click to place them.",
}


def series_key(title):
    """'Duck Life 3' and 'Duck Life' share the key 'duck life'."""
    t = re.sub(r"\s*\((?:Version \d+|[^)]*)\)\s*$", "", title)
    t = re.sub(r"[:\-–].*$", "", t) if ":" in t else t
    t = re.sub(r"\s+(\d+|II|III|IV|VI|VII|X\d?|Part \d+.*)$", "", t)
    return t.lower().strip()


class Copy:
    def __init__(self, games, cats, written):
        self.G = {g["slug"]: g for g in games}
        self.C = {c["slug"]: c for c in cats}
        self.written = {k: v for k, v in written.items() if not k.startswith("_") and v}
        self.series = {}
        for g in games:
            self.series.setdefault(series_key(g["title"]), []).append(g["slug"])

    def siblings(self, g):
        return [s for s in self.series.get(series_key(g["title"]), []) if s != g["slug"]]

    def has_writeup(self, slug):
        return slug in self.written

    # --- game pages ---------------------------------------------------------------------------
    def game_title(self, g):
        t = g["title"]
        full = f"{t} - Play Online for Free | ArcadeWebsite"
        return full if len(full) <= 65 else f"{t} - Play Free Online"

    def game_summary(self, g):
        if g["slug"] in self.written:
            return self.written[g["slug"]][0]
        cat = g["category"]
        return pick(ABOUT[cat], g["slug"]).format(t=g["title"])

    def game_meta(self, g):
        t, cat = g["title"], NOUN[g["category"]]
        if g["slug"] in self.written:
            lead = first_sentence(self.written[g["slug"]][0])
            return clip(f"{lead} Play {t} free online, no download needed.", 158)
        options = [
            f"Play {t} online for free. {t} is a {cat} game that runs right in your browser on ArcadeWebsite, with no download or sign-up needed.",
            f"Play {t} free in your browser. Jump into this {cat} game on ArcadeWebsite instantly, with no download, then discover more {cat} games.",
            f"{t} is a free {cat} game you can play online at ArcadeWebsite. No download, no sign-up: just click Play and start.",
        ]
        return clip(pick(options, g["slug"]), 158)

    def game_paragraphs(self, g, related_titles):
        """The 'About' section: what the game is, plus context that's true for this game."""
        cat = self.C[g["category"]]
        paras = [self.game_summary(g)]
        sib = self.siblings(g)
        if sib:
            paras.append(f"{g['title']} is part of a series on ArcadeWebsite with {len(sib)} other "
                         f"{'game' if len(sib) == 1 else 'games'}, listed below, so you can keep playing when you finish this one.")
        if related_titles:
            names = ", ".join(related_titles[:3])
            paras.append(pick([
                f"If you enjoy {g['title']}, you might also like {names}. You'll find every {cat['name'].lower()} game in our {cat['name']} collection.",
                f"Liked {g['title']}? Try {names} next, or browse the full {cat['name']} collection.",
                f"Looking for something similar to {g['title']}? {names} are good next picks from the {cat['name']} collection.",
            ], g["slug"] + "r"))
        return paras

    def game_howto(self, g):
        if g["slug"] in self.written and len(self.written[g["slug"]]) > 1:
            return self.written[g["slug"]][1]
        return HOWTO[g["category"]]

    def game_faq(self, g, related):
        t, cat = g["title"], self.C[g["category"]]
        faq = [
            (f"Is {t} free to play?", f"Yes. {t} is free to play on ArcadeWebsite, with no sign-up needed."),
            (f"Do I need to download {t}?", f"No. {t} runs in your web browser. Click Play on this page to start."),
            (f"What kind of game is {t}?", f"{t} is in our {cat['name']} collection of {len(cat['games']):,} free games."),
        ]
        if related:
            faq.append((f"What games are like {t}?", "Similar games include " + ", ".join(G_t for G_t in related[:4]) + "."))
        return faq

    # --- category pages ------------------------------------------------------------------------
    def category_title(self, c):
        return f"{c['name']} Games - Play Free Online {c['name']} Games | ArcadeWebsite" if len(c["name"]) < 9 else f"{c['name']} Games - Play Free Online | ArcadeWebsite"

    def category_meta(self, c):
        top = [self.G[s]["title"] for s in c["games"] if s in self.written][:3]
        extra = f" Includes {', '.join(top)} and more." if top else ""
        return clip(f"Play {len(c['games']):,} free {c['name'].lower()} games online at ArcadeWebsite, no download needed.{extra}", 158)
