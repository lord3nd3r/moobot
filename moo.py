# -*- coding: utf-8 -*-
"""
Ultimate Moo Plugin for Sopel IRC Bot
The final evolution. Accept no substitutes.
Now with sudo moo, milestones, leaderboards, and existential dread.
"""
from sopel import plugin
import random
import re
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)
BOT_NICK_LOWER = None

# === VERSION CHECK FOR DB COMPATIBILITY ===
def has_session(bot):
    return hasattr(bot.db, 'session')

# === SETUP: Create table + cache bot nick ===
def setup(bot):
    global BOT_NICK_LOWER
    BOT_NICK_LOWER = bot.nick.lower()

    try:
        if has_session(bot):
            with bot.db.session() as session:
                session.execute(text('''
                    CREATE TABLE IF NOT EXISTS moo_counts (
                        nick TEXT PRIMARY KEY,
                        count INTEGER DEFAULT 0
                    )
                '''))
                session.commit()
        else:
            conn = bot.db.connect()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS moo_counts (
                    nick TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
            conn.close()
        logger.info("Moo table ready. The herd awakens.")
    except Exception as e:
        logger.error(f"Moo setup failed: {e}")

# === DB HELPER ===
def db_helper(bot, nick, operation='get', value=0):
    if not nick:
        return -1

    bot_nick = BOT_NICK_LOWER or bot.nick.lower()
    if nick.lower() == bot_nick:
        return -1

    nick = nick.lower().strip()

    try:
        if has_session(bot):
            with bot.db.session() as session:
                if operation == 'get':
                    result = session.execute(
                        text("SELECT count FROM moo_counts WHERE nick = :nick"),
                        {"nick": nick}
                    ).fetchone()
                    return result[0] if result else 0

                elif operation == 'inc':
                    current = session.execute(
                        text("SELECT count FROM moo_counts WHERE nick = :nick"),
                        {"nick": nick}
                    ).fetchone()
                    new_count = (current[0] if current else 0) + value
                    session.execute(
                        text("""
                            INSERT INTO moo_counts (nick, count)
                            VALUES (:nick, :count)
                            ON CONFLICT(nick) DO UPDATE SET count = :count
                        """),
                        {"nick": nick, "count": new_count}
                    )
                    session.commit()
                    return new_count

        else:
            conn = bot.db.connect()
            cursor = conn.cursor()
            if operation == 'get':
                cursor.execute("SELECT count FROM moo_counts WHERE nick = ?", (nick,))
                row = cursor.fetchone()
                conn.close()
                return row[0] if row else 0

            elif operation == 'inc':
                cursor.execute("SELECT count FROM moo_counts WHERE nick = ?", (nick,))
                row = cursor.fetchone()
                new_count = (row[0] if row else 0) + value
                if row:
                    cursor.execute(
                        "UPDATE moo_counts SET count = ? WHERE nick = ?",
                        (new_count, nick)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO moo_counts (nick, count) VALUES (?, ?)",
                        (nick, new_count)
                    )
                conn.commit()
                conn.close()
                return new_count

    except Exception as e:
        logger.error(f"DB error: {e}")
        return -1

# === CHAOS ARSENAL ===
moos = [
    "Moo", "Moooooo", "MOOOOOO", "Moo?", "Moo Moo", "MOOOOO!", "mOoOoO", "Moooooooo!",
    "SuperMoo!", "Moo-calypse now!", "Schrödingcow says moo and not-moo", "sudo moo",
    "Moo on the rocks", "404: Moo not found", "Moo.exe has stopped responding",
    "Live, laugh, moo", "Moo-mentum conserved", "Moo++", "Quantum moo observed!"
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

MOO_PATTERN = re.compile(r'\b(m+o+)\b', re.IGNORECASE)

# === MAIN MOO TRIGGER ===
@plugin.rule(r'\b(m+o+)\b')
@plugin.rate(6, 15)  # Max 6 triggers per 15 seconds per user
def moo_response(bot, trigger):
    nick = trigger.nick
    if not nick:
        return

    bot_nick = BOT_NICK_LOWER or bot.nick.lower()
    if nick.lower() == bot_nick:
        return

    bot.say(random.choice(moos))
    count = db_helper(bot, nick, 'inc', 1)

    if count > 0 and count in MILESTONES:
        bot.say(f"MOOOOOOOO! {nick} just hit {count:,} moos! {MILESTONES[count]}")

# === SUDO MOO EASTER EGG ===
@plugin.rule(r'(?i)^sudo moo$')
@plugin.rate(1, 30)
def sudo_moo(bot, trigger):
    nick = trigger.nick
    if not nick:
        return

    bot_nick = BOT_NICK_LOWER or bot.nick.lower()
    if nick.lower() == bot_nick:
        return

    bot.say("Super Cow Powers activated!")
    # moo_response will also fire and add +1, so this makes it +10 total
    db_helper(bot, nick, 'inc', 9)

# === LEADERBOARDS ===
def _show_top(bot, trigger, limit=10):
    try:
        if has_session(bot):
            with bot.db.session() as s:
                rows = s.execute(
                    text("""
                        SELECT nick, count
                        FROM moo_counts
                        ORDER BY count DESC, nick ASC
                        LIMIT :limit
                    """),
                    {"limit": limit}
                ).fetchall()
        else:
            conn = bot.db.connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nick, count FROM moo_counts "
                "ORDER BY count DESC, nick ASC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            conn.close()

        if not rows:
            bot.say("No moos yet. Sad cow.")
            return

        bot_nick = BOT_NICK_LOWER or bot.nick.lower()
        lines = [f"Top {limit} Moo Legends:"]
        for n, c in rows:
            if n.lower() == bot_nick:
                continue
            lines.append(f"• {n}: {c:,} moos")

        message = " | ".join(lines)
        if len(message) > 400:
            # crude split if it gets too long
            bot.say(" | ".join(lines[:3]))
            bot.say(" | ".join(lines[3:]))
        else:
            bot.say(message)

    except Exception as e:
        bot.say("The leaderboard is drunk on milk.")
        logger.error(f"Leaderboard error: {e}")

@plugin.commands('mootop', 'topmoo')
def mootop(bot, trigger):
    _show_top(bot, trigger, 20)

@plugin.commands('mootop10', 'topmoo10')
def mootop10(bot, trigger):
    _show_top(bot, trigger, 10)

@plugin.commands('mootop5', 'topmoo5')
def mootop5(bot, trigger):
    _show_top(bot, trigger, 5)

# === COMMANDS ===
@plugin.commands('moocount', 'mymoo', 'moos')
def moocount(bot, trigger):
    c = db_helper(bot, trigger.nick)
    if c >= 0:
        plural = "time" if c == 1 else "times"
        bot.say(f"{trigger.nick} has mooed {c:,} {plural}.")
    else:
        bot.say("Moo counter broken. Cows on strike.")

@plugin.commands('totalmoo', 'moostats')
def totalmoo(bot, trigger):
    try:
        if has_session(bot):
            with bot.db.session() as s:
                total = s.execute(
                    text("SELECT SUM(count) FROM moo_counts")
                ).scalar() or 0
                users = s.execute(
                    text("SELECT COUNT(*) FROM moo_counts")
                ).scalar() or 0
        else:
            conn = bot.db.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(count), COUNT(*) FROM moo_counts")
            total, users = cursor.fetchone()
            total = total or 0
            users = users or 0
            conn.close()

        bot.say(
            f"Total moos: {total:,} from {users} "
            f"{'cow' if users == 1 else 'cows'}!"
        )
    except Exception as e:
        logger.error(f"totalmoo error: {e}")
        bot.say("The cows ate the stats.")

@plugin.commands('moohelp', 'aboutmoo')
def moohelp(bot, trigger):
    # Update this if you change your prefix; assuming $ (escaped in config as \$
    bot.say(
        "Moo v3.1 | Say 'moo' → moo back | "
        "$mootop / $mootop10 / $mootop5 | "
        "$moocount | $totalmoo | 'sudo moo' = +10 moos | "
        "Pure chaos, zero regrets."
    )

# === ADMIN: RESET MOO COUNT ===
@plugin.command('resetmoo')
@plugin.require_admin()
def resetmoo(bot, trigger):
    target = trigger.group(2)
    if not target:
        bot.reply("Usage: $resetmoo <nick>")
        return

    target_norm = target.lower().strip()
    try:
        if has_session(bot):
            with bot.db.session() as s:
                result = s.execute(
                    text("DELETE FROM moo_counts WHERE nick = :n"),
                    {"n": target_norm}
                )
                s.commit()
                deleted = result.rowcount
        else:
            conn = bot.db.connect()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM moo_counts WHERE nick = ?",
                (target_norm,)
            )
            deleted = cursor.rowcount
            conn.commit()
            conn.close()

        if deleted:
            bot.say(f"Moo record for {target} erased.")
        else:
            bot.say(f"No record for {target}.")
    except Exception as e:
        logger.error(f"resetmoo error: {e}")
        bot.say("Reset failed. The cows resisted.")
