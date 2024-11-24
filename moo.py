from sopel import plugin
import random
import re
import threading
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database setup and helper functions
def db_setup(bot):
    conn = bot.db.connect()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS moo_counts (
                nick TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        logger.debug("Moo counts table created or already exists.")
    except Exception as e:
        logger.error(f"Database error in setup: {e}")
    finally:
        conn.close()

# Helper function to interact with the database
def db_helper(bot, nick, operation='get', value=0):
    lock = threading.Lock()
    with lock:
        conn = bot.db.connect()
        try:
            cursor = conn.cursor()
            if operation == 'get':
                # Fetch moo count for the user
                cursor.execute('SELECT count FROM moo_counts WHERE nick = ?', (nick,))
                row = cursor.fetchone()
                if row:
                    logger.debug(f"Retrieved count for {nick}: {row[0]}")
                    return row[0]
                else:
                    logger.debug(f"No count found for {nick}, initializing to 0.")
                    return 0
            elif operation == 'inc':
                # Increment moo count for the user
                cursor.execute('SELECT count FROM moo_counts WHERE nick = ?', (nick,))
                row = cursor.fetchone()
                if row:
                    new_count = row[0] + value
                    cursor.execute('UPDATE moo_counts SET count = ? WHERE nick = ?', (new_count, nick))
                    logger.debug(f"Updated count for {nick}: {new_count}")
                else:
                    new_count = value
                    cursor.execute('INSERT INTO moo_counts (nick, count) VALUES (?, ?)', (nick, new_count))
                    logger.debug(f"Inserted new count for {nick}: {new_count}")
                conn.commit()
                return new_count
        except Exception as e:
            logger.error(f"Database error in db_helper: {e}")
            return -1
        finally:
            conn.close()

# Setup function to create the table
def setup(bot):
    db_setup(bot)
    logger.debug("Setting up the moo plugin.")

# Moo responses with variations
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
    # New responses
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
    'Moo-sical chairs!', 'Moo-ble in space!', 'Moo-nkin’ around!', 
    'Moo-mentous occasion!', 'Mooo are the champions!'
]

# Moo response with improved regex handling
@plugin.rule(r'\b(m+o+)\b')
def moo_response(bot, trigger):
    logger.debug(f"Triggered moo_response by {trigger.nick}.")
    if trigger.nick == bot.nick:
        return

    # Check for the pattern case-insensitively
    pattern = re.compile(r'\b(m+o+)\b', re.IGNORECASE)
    match = pattern.search(trigger.group(0))
    if not match:
        return

    bot.say(random.choice(moos))

    count = db_helper(bot, trigger.nick.lower(), 'inc', 1)
    if count >= 0:
        if count == 1:
            bot.say(f"Welcome {trigger.nick}! That's your first moo!")
    else:
        bot.say(f"Sorry {trigger.nick}, something went wrong while updating your moo count.")

# Command to display the top 20 users with the highest moo counts
@plugin.command('mootop', 'topmoo')
def mootop(bot, trigger):
    logger.debug("Triggered mootop command.")
    conn = None  # Initialize connection to handle properly
    try:
        conn = bot.db.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT nick, count FROM moo_counts ORDER BY count DESC, nick ASC LIMIT 20')
        rows = cursor.fetchall()
        logger.debug(f"Top 20 moo counts retrieved: {rows}")
    except Exception as e:
        logger.error(f"Database error in mootop: {e}")
        bot.say("Sorry, I'm having trouble accessing the moo records right now.")
        return
    finally:
        if conn:
            conn.close()  # Ensure the connection is closed properly

    if not rows:
        bot.say("No one has mooed yet!")
        return

    message = "Top Moos:"
    logger.debug(f"Preparing message with {len(rows)} entries")
    for nick, count in rows:
        entry = f" {nick}: {count},"
        if len(message + entry) > 400:
            bot.say(message.rstrip(','), trigger.sender)
            logger.debug(f"Sent partial message: {message.rstrip(',')}")
            message = entry.strip()
        else:
            message += entry
    bot.say(message.rstrip(','), trigger.sender)
    logger.debug(f"Sent final message: {message.rstrip(',')}")

# Command to show the user's own moo count privately (via PM)
@plugin.command('moocount', 'mymoo')
def moocount(bot, trigger):
    logger.debug(f"Triggered moocount for {trigger.nick}.")
    count = db_helper(bot, trigger.nick.lower())
    if count >= 0:
        bot.notice(f"You have mooed {count} times.", trigger.nick)  # Corrected order
        logger.debug(f"Sent notice to {trigger.nick} with their moo count: {count}")
    else:
        bot.notice(f"Sorry {trigger.nick}, I'm having trouble accessing your moo count right now.", trigger.nick)  # Corrected order
