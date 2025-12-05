# -*- coding: utf-8 -*-
"""
Ultimate Moo Plugin for Sopel – v3.4 – Legendary Edition
"""

from sopel import plugin
import random
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)
BOT_NICK_LOWER = None

def get_config(bot, option, default=None):
    parser = getattr(bot.config, "parser", None)
    if not parser or not parser.has_section("moo"):
        return default
    if not parser.has_option("moo", option):
        return default
    val = parser.get("moo", option).strip().lower()
    if val in ("true", "yes", "on", "1"):
        return True
    if val in ("false", "no", "off", "0"):
        return False
    try:
        return int(val)
    except ValueError:
        return parser.get("moo", option).strip()

def setup(bot):
    global BOT_NICK_LOWER
    BOT_NICK_LOWER = bot.nick.lower()

    parser = getattr(bot.config, "parser", None)
    if parser:
        if not parser.has_section("moo"):
            parser.add_section("moo")
        if not parser.has_option("moo", "leet_moo"):
            parser.set("moo", "leet_moo", "true")

    try:
        if hasattr(bot.db, "session"):
            with bot.db.session() as s:
                s.execute(text("""
                    CREATE TABLE IF NOT EXISTS moo_counts (
                        nick TEXT PRIMARY KEY,
                        count INTEGER DEFAULT 0
                    )
                """))
                s.commit()
        else:
            conn = bot.db.connect()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS moo_counts (
                    nick TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            conn.close()
    except Exception as e:
        logger.error(f"Moo setup error: {e}")

def db_helper(bot, nick, op="get", val=0):
    nick = nick.strip().lower()
    if nick == (BOT_NICK_LOWER or bot.nick.lower()):
        return -1
    try:
        if hasattr(bot.db, "session"):
            with bot.db.session() as s:
                if op == "get":
                    row = s.execute(
                        text("SELECT count FROM moo_counts WHERE nick = :n"),
                        {"n": nick},
                    ).fetchone()
                    return row[0] if row else 0
                row = s.execute(
                    text("SELECT count FROM moo_counts WHERE nick = :n"),
                    {"n": nick},
                ).fetchone()
                new = (row[0] if row else 0) + val
                s.execute(
                    text("""
                        INSERT INTO moo_counts (nick, count) VALUES (:n, :c)
                        ON CONFLICT(nick) DO UPDATE SET count = :c
                    """),
                    {"n": nick, "c": new},
                )
                s.commit()
                return new
        else:
            conn = bot.db.connect()
            cur = conn.cursor()
            cur.execute("SELECT count FROM moo_counts WHERE nick = ?", (nick,))
            row = cur.fetchone()
            new = (row[0] if row else 0) + val
            cur.execute(
                "INSERT OR REPLACE INTO moo_counts (nick, count) VALUES (?, ?)",
                (nick, new),
            )
            conn.commit()
            conn.close()
            return new
    except Exception as e:
        logger.error(f"DB error: {e}")
        return -1

# === Your original moos list, unchanged ===
moos = [
    "Moo","Moooooo","MOOOOOO","Moo?","Moo Moo","MOOOOO!","mOoOoO","Moooooooo!","SuperMoo!",
    "Moo-calypse now!","Schrödingcow","sudo moo","Moo on the rocks","404: Moo not found",
    "Moo.exe has stopped responding","Live, laugh, moo","Moo-mentum conserved","Moo++",
    "m0000000000000000","MOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO","Moo²","Moo³",
    "Moo is love, moo is life","Cowabunga!","MooCoin to the mooooon","MooBERT",
    "There is no cloud. It's just someone else's pasture.","ELON JUST TWEETED A COW EMOJI",
    "Kernel panic: not enough moo","Segmoo fault","docker run moo","systemctl restart cows",
    "More cowbell!","Quantum cow","The final moo is not the end"
] * 3  # 93 total

# === New: rare legendary moos (worth +20) ===
legendary_moos = [
    "🌈 LEGENDARY MOO DROPS FROM THE SKY 🌈",
    "🔥 MOOCRITICAL HIT! 20x DAMAGE! 🔥",
    "✨ Shiny Golden Moo appears! ✨",
    "🌟 Cosmic Cow bellows across the universe: MOOOOOOOO 🌟",
    "💎 Diamond-encrusted Moo echoes through the pasture 💎",
    "⚡ THUNDERMOO STRIKES! The ground trembles... ⚡",
    "🧬 Genetic Supercow says: MOO+MOO = MOO² 🧬",
    "👑 KING OF COWS DECLARES: This is a LEGENDARY MOO 👑",
]

MILESTONES = {
    1: "First moo! The herd welcomes you.",
    10: "Moo Adept achieved!",
    50: "Certified Mooologist",
    100: "Moo Master rank up!",
    500: "Legendary Cow status: UNLOCKED",
    1000: "MOO GOD HAS AWAKENED",
    2000: "The cows are writing fanfics about you now",
    5000: "Global moo shortage declared",
    10000: "ELON JUST TWEETED: 'this guy moos too much'"
}

@plugin.rule(r"\b(m[0o]+)\b")
@plugin.rate(user=6, channel=15)  # FIXED: "time" -> "channel"
def moo_response(bot, trigger):
    if not trigger.nick or trigger.nick.lower() == bot.nick.lower():
        return
    if not get_config(bot, "leet_moo", True) and "0" in trigger.group(0):
        return

    # ~2% chance for a legendary moo; tweak probability if you want
    legendary = random.random() < 0.02

    if legendary:
        msg = random.choice(legendary_moos)
        inc = 20
    else:
        msg = random.choice(moos)
        inc = 1

    bot.say(msg)

    count = db_helper(bot, trigger.nick, "inc", inc)

    if legendary and count >= 0:
        bot.say(
            f"LEGENDARY MOO! {trigger.nick} gains +{inc} moos at once "
            f"(total: {count:,})!"
        )

    if count > 0 and count in MILESTONES:
        bot.say(f"MOOOOOOOO! {trigger.nick} just hit {count:,} moos! {MILESTONES[count]}")

@plugin.rule(r"(?i)^sudo moo$")
@plugin.rate(1, 30)
def sudo_moo(bot, trigger):
    if not trigger.nick or trigger.nick.lower() == bot.nick.lower():
        return
    bot.say("Super Cow Powers activated!")
    db_helper(bot, trigger.nick, "inc", 9)

@plugin.commands("moocount", "mymoo", "moos")
def moocount(bot, trigger):
    target = trigger.group(2).strip() if trigger.group(2) else trigger.nick
    c = db_helper(bot, target, "get")
    if c >= 0:
        bot.say(f"{target} has mooed {c:,} time{'s' if c != 1 else ''}.")
    else:
        bot.say("Moo counter broken.")

@plugin.commands("mootop", "topmoo")
def mootop(bot, trigger):
    try:
        limit = int((trigger.group(2) or "10").strip().split()[0])
    except Exception:
        limit = 10
    limit = max(1, min(50, limit))
    try:
        if hasattr(bot.db, "session"):
            with bot.db.session() as s:
                rows = s.execute(
                    text("SELECT nick, count FROM moo_counts "
                         "ORDER BY count DESC, nick LIMIT :l"),
                    {"l": limit},
                ).fetchall()
        else:
            conn = bot.db.connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT nick, count FROM moo_counts "
                "ORDER BY count DESC, nick LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            conn.close()
        lines = [f"Top {limit} Moo Legends:"]
        for n, c in rows:
            if n.lower() == bot.nick.lower():
                continue
            lines.append(f"• {n}: {c:,}")
        bot.say(" | ".join(lines))
    except Exception:
        bot.say("Leaderboard error.")

@plugin.commands("totalmoo", "moostats")
def totalmoo(bot, trigger):
    try:
        if hasattr(bot.db, "session"):
            with bot.db.session() as s:
                total = s.execute(
                    text("SELECT SUM(count) FROM moo_counts")
                ).scalar() or 0
        else:
            conn = bot.db.connect()
            cur = conn.cursor()
            cur.execute("SELECT SUM(count) FROM moo_counts")
            total = cur.fetchone()[0] or 0
            conn.close()
        bot.say(f"Total moos: {total:,}.")
    except Exception:
        bot.say("Total failed.")

@plugin.commands("mooreset")
@plugin.require_admin()
def mooreset(bot, trigger):
    target = trigger.group(2).strip() if trigger.group(2) else None
    try:
        if hasattr(bot.db, "session"):
            with bot.db.session() as s:
                if target:
                    s.execute(
                        text("DELETE FROM moo_counts WHERE nick = :n"),
                        {"n": target.lower()},
                    )
                else:
                    s.execute(text("DELETE FROM moo_counts"))
                s.commit()
        else:
            conn = bot.db.connect()
            if target:
                conn.execute(
                    "DELETE FROM moo_counts WHERE nick = ?",
                    (target.lower(),),
                )
            else:
                conn.execute("DELETE FROM moo_counts")
            conn.commit()
            conn.close()
        bot.say("Reset done." if not target else f"Reset {target}.")
    except Exception:
        bot.say("Reset failed.")

@plugin.commands("moohelp", "aboutmoo")
def moohelp(bot, trigger):
    leet = "ON" if get_config(bot, "leet_moo", True) else "OFF"
    bot.say(
        "Moo v3.4 Legendary | "
        f"Leet-moo {leet} | moo/m000 → reply (rare LEGENDARY moos worth +20!) | "
        "sudo moo = +10 | .moocount .mootop .totalmoo .mooreset"
    )
