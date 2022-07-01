# Skill of the Week bot
#### Author: kgasiorowski

## Setting up the bot
1. Invite the bot to your discord server [here](https://www.google.com) 
2. Set the prefix you'd like to use for this bot using `setprefix <prefix>`
3. Use `setadminchannnel` and `setadminrole` to set the admin channel and role, respectively, for the bot. If you dont set these then anyone will be able to run any command from anywhere.
4. Use `setpublicchannel` to set the public bot channel.
5. Read the rest of this document to familiarize yourself with the commands available to admins and general users.

## Commands
### General

- `register <username>` - links the discord user to a runescape username
- `status` - reports the current SOTW status

### Admin

- `setprefix <prefix>` - sets the prefix for the bot. By default it is not set, so the bot will treat every message as a command until you set a prefix.
- `setadminrole @<role>` - sets the role that is allowed to run SOTW bot admin commands. If this isn't set, then it will default to any role with `admin` in the name.
- `setadminchannel #<channel>` - sets the channel in which admins can interact with the bot. If it's not set, then admins can interact with it anywhere
- `setpublichannel #<channel>` - sets the channel in which general discord members can interact with the bot. If not set, the bot will listen in all channels and respond everywhere.
- `settitle <SOTW title>` - sets the title for the next SOTW that is created
- `setgroup <group id> <verification code>` - sets the player group for the sotw. (Optional)
- `openpoll <skills>` - opens a poll for users to vote on the next skill of the week skill. Expects skills after the command, for example: `openpoll woodcutting fishing thieving`.
- `closepoll` - closes the currently opened poll, records, the winner, and saves it to the configs. When the next sotw is created, this skill will be automatically chosen.
- `createsotw <date> <duration> <skill>` - schedules a SOTW to start on the given day, with the given duration, for the given skill. 
  - `<date>` is expected to be in descending order, or, `YYYY/MM/DD`
  - `<duration>` is expected to be something like the following
    - `1d` - signifies one day
    - `2w` - signifies two weeks
    - etc
  - `<skill>` is the skill that this SOTW will be. This is optional, if there was one already polled and saved.
- `deletesotw` - if you've accidentally created a SOTW and need to backtrack, use this command to completely delete the current SOTW for this server. Beware, this cannot be reversed by any means.
- `closesotw` - closes the current SOTW. This congratulates the top three and pings the winner with a list of eligible skills for the next SOTW. After they've chosen, the bot automatically opens a poll which the rest of the server can vote on.
- `reloadconfigs` - reloads configurations after they were manually changed on the server. Mostly used for development.

## TDLR - just let me set up a SOTW

1. Read the `Setting up the bot` section above
2. Select three skills you'd like to poll and create a poll using `openpoll` - **optional**
3. Allow the server to vote on the proposed skills for a few days - **optional**
4. Close the poll with `closepoll`, this will automatically check for the most voted for skill and save it for later - **optional**
5. Give your SOTW a title with `settitle`
6. Create the SOTW with `createsotw` (if you didn't poll a skill earlier, you can just pass one in with this command)
7. Wait for the SOTW to end
8. End the sotw with `closesotw`
9. The bot will directly message the winner of the event and allow them to choose the poll options for the next event.
10. Go back to step 3.