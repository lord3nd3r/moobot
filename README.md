Sopel Moo Counter Plugin

This plugin for the Sopel IRC bot adds fun responses to any variations of "moo" that users type in chat, while also tracking the number of times each user has said "moo."
Features

    Responds with a random "moo" variation when users type any form of "moo" in the channel.
    Tracks the number of times each user has said "moo."
    Allows users to check their own moo count.
    Displays the top 20 users with the highest moo counts.

Commands

    Automatic "Moo" Responses: Whenever a user types any variation of "moo" (e.g., "mooo," "mOoOo"), the bot will respond with a random moo variation from a predefined list.

    !topmoo or !mootop: Displays the top 20 users with the highest moo counts in the channel. (depending on the sopel trigger)

    !moocount or !mymoo: Sends a private message to the user with their current moo count. (depending on the sopel trigger)

Installation

    Clone this repository or download the plugin file directly.
    Copy the plugin file to your Sopel bot's plugin directory, typically located at ~/.sopel/plugins/.
    Ensure the plugin is recognized by adding it to the sopel.cfg file under the [core] section (if needed).
    Restart your Sopel bot to load the plugin.

Configuration

No additional configuration is required for this plugin. It automatically sets up the database and starts tracking users' moo counts when activated.
Usage

Once the plugin is installed and your bot is running, users in the channel can start typing "moo" to interact with the bot. You can use the following commands:

    !topmoo: Shows the top 20 users by moo count.  (depending on the sopel trigger)
    !moocount: Get your personal moo count via private message.  (depending on the sopel trigger)

Example

<user1> moo
<bot> Mooooooo!
<bot> Welcome user1! That's your first moo!

<user2> mooo
<bot> Moo Moo Moo!
<user2> !moocount
<bot> (via PM): You have mooed 1 time.

License

This project is licensed under the MIT License. See the LICENSE file for more details.
Contributing

Feel free to fork this repository and submit pull requests with new features, bug fixes, or any other improvements!
