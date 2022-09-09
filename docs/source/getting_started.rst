Getting Started
===============

Bot of Spades is ready already; all you need to do is run it. First, download
`the repository <https://github.com/volatusveritas/bot-of-spades>`_'s contents
either directly or by cloning it. Next, create two special files (in the bot's
root directory) the bot needs in order to run properly:

1. ``.BOT_TOKEN``: this file should contain only one line with the bot's token
   and nothing else.
2. ``.SERVER_ID``: currently, registering a global slash command is slow; from
   the moment you first run your bot, it'll take a good while before the
   commands are available. A better option if you're running this bot in a
   local, small server or if you're developing is to specify a server for the
   bot to register commands to (in which case they are registered instantly).
   To do so, in the root directory of the repository, create a file called
   ``.SERVER_ID`` and place in it the target server's ID inside of it, in one
   line, and nothing else.

Now, to run it, you can simply do:

.. code-block::

   python -m botofspades

Or, if you don't want it to cache binaries (``.pyc`` files), use:

.. code-block::

   python -B -m botofspades

You should now have the bot up and running.
