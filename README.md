# Skill of the Week bot
#### Author: kgasiorowski

---

## Setting up the bot
1. Invite the bot to your discord server [here](https://www.google.com) 
2. Set the prefix you'd like to use for this bot using `setprefix <prefix>`
3. Use `setadminchannnel` and `setadminrole` to set the admin channel and role, respectively, for the bot. If you dont set these then anyone will be able to run any command from anywhere.
4. Use `setpublicchannel` to set the public bot channel.
5. Read the rest of this document to familiarize yourself with the commands available to admins and general users.
---
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
- `setgroup <group id> <verification code>` - sets the group for the sotw. (Optional)
- `createsotw <date> <duration> <skill>` - schedules a SOTW to start on the given day, with the given duration, for the given skill. 
  - `<date>` is expected to be in descending order, or, `YYYY/MM/DD`
  - `<duration>` is expected to be something like the following
    - 1d - signifies one day
    - 2w - signifies two weeks
    - etc
  - `<skill>` is the skill that this SOTW will be. This is optional, if there was one already polled and saved. More on polls later.
- `reloadconfigs` - reloads configurations after they were manually changed on the server. Mostly used for development.