# -*- coding: utf-8 -*-
"""
Moo Plugin for Sopel IRC Bot
Compatible with Sopel 7.x and 8.x+
"""
from sopel import plugin
import random
import re
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# === VERSION CHECK FOR DB COMPATIBILITY ===
def has_session(bot):
    return hasattr(bot.db, 'session')

# === SETUP: Create table ===
def setup(bot):
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
            logger.debug("Moo table created via session.")
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
            logger.debug("Moo table created via connect().")
    except Exception as e:
        logger.error(f"Database setup error: {e}")

# === DB HELPER ===
def db_helper(bot, nick, operation='get', value=0):
    if not nick:
        logger.warning("db_helper called with empty nick!")
        return -1
    nick = nick.lower().strip()
    logger.debug(f"db_helper: nick='{nick}', op='{operation}', value={value}")

    try:
        if has_session(bot):
            with bot.db.session() as session:
                if operation == 'get':
                    result = session.execute(
                        text('SELECT count FROM moo_counts WHERE nick = :nick'),
                        {'nick': nick}
                    ).fetchone()
                    count = result[0] if result else 0
                    logger.debug(f"GET: {nick} = {count}")
                    return count

                elif operation == 'inc':
                    result = session.execute(
                        text('SELECT count FROM moo_counts WHERE nick = :nick'),
                        {'nick': nick}
                    ).fetchone()
                    if result:
                        new_count = result[0] + value
                        session.execute(
                            text('UPDATE moo_counts SET count = :count WHERE nick = :nick'),
                            {'count': new_count, 'nick': nick}
                        )
                    else:
                        new_count = value
                        session.execute(
                            text('INSERT INTO moo_counts (nick, count) VALUES (:nick, :count)'),
                            {'nick': nick, 'count': new_count}
                        )
                    session.commit()
                    logger.debug(f"INC: {nick} → {new_count}")
                    return new_count

        else:
            # Raw SQLite fallback
            conn = bot.db.connect()
            cursor = conn.cursor()
            if operation == 'get':
                cursor.execute('SELECT count FROM moo_counts WHERE nick = ?', (nick,))
                row = cursor.fetchone()
                count = row[0] if row else 0
                conn.close()
                return count
            elif operation == 'inc':
                cursor.execute('SELECT count FROM moo_counts WHERE nick = ?', (nick,))
                row = cursor.fetchone()
                if row:
                    new_count = row[0] + value
                    cursor.execute('UPDATE moo_counts SET count = ? WHERE nick = ?', (new_count, nick))
                else:
                    new_count = value
                    cursor.execute('INSERT INTO moo_counts (nick, count) VALUES (?, ?)', (nick, new_count))
                conn.commit()
                conn.close()
                return new_count
    except Exception as e:
        logger.error(f"Database error in db_helper: {e}")
        return -1

# === MOO RESPONSES ===
moos = [
    'Moo', 'Moooo', 'Moooooo', 'Mooooooo', 'Mooooo!', 'Moo?', 'Moooooo...',
    'Moo Moo', 'MOOOO!', 'Moooooo... Moo?', 'Moooooooo!', 'mOoOoO',
    'Mooooooooooooooooo!', 'Mooing intensely!', 'Moo-fantastic!',
    'Moo Moo Moo!', 'Mooooooooooow!', 'Moo, but dramatic', 'Mini-moo',
    'Mega-MOO', 'SuperMoo!', 'Moo-mendous!', 'Moo-tacular!', 'Moo-yay!',
    'Moo-verload!', 'Moo-mazing!', 'Moo-velous!', 'Moo-nificent!',
    'Moo-rific!', 'Moo-valanche!', 'Moo-tropolis!', 'Moo-gantic!',
    'Mooooo! (urgent)', 'MOOOO, REPEAT:', 'MOOOOO', 'MOOOOOO...',
    'MOOOOOOO', 'Moooooo?!', 'Meeee-mooo!', 'meh-mooooo.', 'MMOOOOO',
    'Moooo...?', 'MOOOOOOOOO', 'moOOOo...', 'MoooOOO', 'MoooOOoo',
    'MOOOOOM:', 'MOOOOMMmmm',
    'Moo-tastic surprise!', 'Moo-zilla is here!', 'Moooooooh, yeah!',
    'Moo with a twist!', 'Moooo-delicious!', 'Moo-nlight serenade!',
    'Moo-rific explosion!', 'Moo-sical note!', 'Moo-larious!',
    'Moooo from the deep!', 'Moo-vie star!', 'Moo-tanical gardens!',
    'Moo-phoria!', 'Moo-sational!', 'Moo-ment of truth!',
    'Moo-nicorn flair!', 'Moo-nificent vibes!', 'Moo-tion detected!',
    'Moo-tion graphics!', 'Moo-lecular structure!', 'Moo-calypse now!',
    'Moo-rning sunshine!', 'Moo-dinary day!', 'Moo-ving forward!',
    'Moo-licious treat!', 'Mooooo-rific journey!', 'Moo-oh-la-la!',
    'Moo-tiful dreams!', 'Moo-ment of glory!', 'Moo-tivation station!',
    'Moo-rvelous creation!', 'Moo-emorial day!', 'Moo-tion picture!',
    'Mooooove over!', 'Moo-stache power!', 'Moo-style icon!',
    'Moo-sical chairs!', 'Moo-ble in space!', "Moo-nkin' around!",
    'Moo-mentous occasion!', 'Mooo are the champions!',
    'Moo-hemian Rhapsody!', 'Is this the real moo?', 'Moo-ntain high!',
    'Moo-dern art!', 'Moo-tant ninja cow!', 'Moo-llennium falcon!',
    'Moo-nt Everest climbed!', 'Moo-dini escapes!', 'Moo-ving at light speed!'
]

# === MOO TRIGGER ===
@plugin.rule(r'\b(m+o+)\b')
@plugin.rate(3)
def moo_response(bot, trigger):
    nick = trigger.nick
    if not nick or nick.lower() == bot.nick.lower():
        return

    pattern = re.compile(r'\b(m+o+)\b', re.IGNORECASE)
    if not pattern.search(trigger.group(0)):
        return

    bot.say(random.choice(moos))
    count = db_helper(bot, nick, 'inc', 1)

    if count >= 0:
        if count == 1:
            bot.say(f"Welcome {nick}! That's your first moo!")
        elif count in [10, 50, 100, 500, 1000]:
            bot.say(f"Congratulations {nick}! You've mooed {count} times! Cow-mazing!")
    else:
        bot.say(f"Sorry {nick}, something went wrong with your moo count.")

# === TOP MOOERS ===
@plugin.command('mootop', 'topmoo')
def mootop(bot, trigger):
    logger.debug("Triggered mootop")
    try:
        if has_session(bot):
            with bot.db.session() as session:
                rows = session.execute(
                    text('SELECT nick, count FROM moo_counts ORDER BY count DESC, nick ASC LIMIT 20')
                ).fetchall()
        else:
            conn = bot.db.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT nick, count FROM moo_counts ORDER BY count DESC, nick ASC LIMIT 20')
            rows = cursor.fetchall()
            conn.close()
    except Exception as e:
        logger.error(f"DB error in mootop: {e}")
        bot.say("Sorry, moo records are unavailable.")
        return

    if not rows:
        bot.say("No one has mooed yet! Be the first!")
        return

    message = "Top 20 Moos:"
    for nick, count in rows:
        if nick.lower() == bot.nick.lower():
            continue
        entry = f" {nick}: {count},"
        if len(message + entry) > 400:
            bot.say(message.rstrip(','), trigger.sender)
            message = " " + entry.strip()
        else:
            message += entry
    bot.say(message.rstrip(','), trigger.sender)

# === USER MOO COUNT (PM) ===
@plugin.command('moocount', 'mymoo')
def moocount(bot, trigger):
    count = db_helper(bot, trigger.nick)
    if count >= 0:
        plural = 'time' if count == 1 else 'times'
        bot.notice(trigger.nick, f"You have mooed {count} {plural}.")
    else:
        bot.notice(trigger.nick, "Sorry, I couldn't retrieve your moo count.")

# === TOTAL MOO STATS ===
@plugin.command('totalmoo', 'moostats')
def totalmoo(bot, trigger):
    try:
        if has_session(bot):
            with bot.db.session() as session:
                total = session.execute(text('SELECT SUM(count) FROM moo_counts')).scalar() or 0
                users = session.execute(text('SELECT COUNT(nick) FROM moo_counts')).scalar()
        else:
            conn = bot.db.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(count) FROM moo_counts')
            total = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(nick) FROM moo_counts')
            users = cursor.fetchone()[0]
            conn.close()
        plural = 'cow' if users == 1 else 'cows'
        bot.say(f"Total moos: {total} by {users} {plural}!")
    except Exception as e:
        logger.error(f"Error in totalmoo: {e}")
        bot.say("Moo stats unavailable.")

# === ADMIN: RESET MOO COUNT ===
@plugin.command('resetmoo')
@plugin.require_admin()
def resetmoo(bot, trigger):
    target = trigger.group(2)
    if not target:
        bot.reply("Usage: .resetmoo <nick>")
        return
    target_lower = target.lower().strip()
    try:
        if has_session(bot):
            with bot.db.session() as session:
                result = session.execute(
                    text('DELETE FROM moo_counts WHERE nick = :nick'),
                    {'nick': target_lower}
                ).rowcount
                session.commit()
        else:
            conn = bot.db.connect()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM moo_counts WHERE nick = ?', (target_lower,))
            result = cursor.rowcount
            conn.commit()
            conn.close()
        bot.say(f"Moo count reset for {target}." if result else f"No record for {target}.")
    except Exception as e:
        logger.error(f"Reset error: {e}")
        bot.say("Failed to reset.")
