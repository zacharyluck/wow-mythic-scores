// import modules
const Discord = require('discord.js');
const axios = require('axios');

// grab environment files and load them
const dotenv = require('dotenv');
dotenv.config();

// setup client and connection to SQL server
const client = new Discord.Client();

// set prefix for bot to recognize
const prefix = '!wowmst';

let server_url;
let cli_args = '';

// get an arg from CLI to see if I wanna run it locally or not
// TODO: maybe some other args eventually
if (process.argv.length > 2) {
    cli_args = process.argv[2];
}
if (cli_args === '--debug') {
    server_url = 'http://localhost:5000/';
}
else {
    server_url = process.env.SERVER_URL;
}

// report back when bot is ready
client.once('ready', () => {
    if (cli_args) {
        console.log('Discord bot started in debug mode.');
    }
    console.log('Mythic Tracker Bot ready.');
});

// when someone sends a message
client.on('message', message => {
    // if the message doesn't start with the prefix
    // or is from the bot itself, ignore
    if (!message.content.startsWith(prefix) || message.author.bot) return;

    // grab the args of the command
    const args = message.content.slice(prefix.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    console.log(command, args);

    // ----------------------------------------------------
    // command to give instructions to make new spreadsheet
    // ----------------------------------------------------
    if (command === 'new') {
        return message.channel.send(`To set up a spreadsheet, follow the steps below, to link a spreadsheet you've already set up, type "!wowmst link" for help
1. Go to: https://docs.google.com/spreadsheets/d/1_OPGEKPs5EqbgyCXMjHS4krR6A5g1DIfEanS3T-qO4E/edit?usp=sharing

2. Click "File" and click "Make a copy" to save the spreadsheet to your own Google Drive

3. Rename the spreadsheet as follows: \`[Region]_[Realm]_[Guild name]\`
ex: \`US_Garona_Noctum\`

4. Click "Share" and add as an editor the e-mail: \`wow-mst-sa@wow-mythic-score-tracker.iam.gserviceaccount.com\`

Once you've done all that, you should be able to run \`!wowmst link\``);
    }

    // ----------------------------
    // link server with spreadsheet
    // ----------------------------
    if (command === 'link') {
        // no arguments
        if (!args.length) {
            return message.channel.send(`Command usage:
\`!wowmst link [spreadsheet name]\`
\`!wowmst link whatis\`

If you've already set up a spreadsheet via following the instructions of \`!wowmst new\`, you'll use the name you set for that spreadsheet.

Otherwise, \`!wowmst link whatis\` will tell you the current name of the spreadsheet linked to this server.
`);
        }
        // whatis argument, gets current spreadsheet name
        else if (args[0] === 'whatis') {
            // do a get request of the API
            axios.get(server_url + 'link/whatis', {
                params: {
                    id: message.guild.id.toString(),
                    token: process.env.TOKEN,
                },
            })
            .then(res => {
                // process the different responses the API can return.
                if (res.data.startsWith('Success')) {
                    // successful response
                    return message.channel.send('This server\'s linked spreadsheet is: ' + res.data.slice('Success'.length).trim() + '.');
                }
                else if (res.data === 'No link') {
                    // sheet not linked yet
                    return message.channel.send('You haven\'t linked a spreadsheet for this server yet.');
                }
                else {
                    // just in case the API 403s or 500s
                    return message.channel.send('Something went horribly wrong. The bot is probably down.');
                }
            })
            .catch(err => {
                console.log(err);
            });
        }
        // link new spreadsheet
        else {
            // send the get request
            axios.get(server_url + 'link', {
                params: {
                    sheet: args[0],
                    id: message.guild.id.toString(),
                    token: process.env.TOKEN,
                },
            })
            .then(res => {
                if (res.data === 'Success') {
                    // successful response
                    return message.channel.send('Spreadsheet linked, your spreadsheet will now automatically update.');
                }
                else if (res.data === 'Already linked') {
                    // spreadsheet specified is already linked in a different server
                    return message.channel.send('This spreadsheet is already linked in a different server.');
                }
                else if (res.data === 'Same sheet') {
                    // this sheet is already linked to this server
                    return message.channel.send('This spreadsheet is already linked here, you\'re good to go!');
                }
                else {
                    // just in case the API 403s or 500s
                    return message.channel.send('Something went horribly wrong. The bot is probably down.');
                }
            })
            .catch(err => {
                console.log(err);
            });
        }
    }

    // --------------------------------
    // get top 10 players for each role
    // --------------------------------
    if (command === 'top10') {
        axios.get(server_url + 'top10', {
            params: {
                id: message.guild.id.toString(),
                token: process.env.TOKEN,
            },
        })
        .then(res => {
            if (res.data === 'No link') {
                // sheet not in SQL
                return message.channel.send('You haven\'t linked a spreadsheet yet, have you set one up via `!wowmst new` and linked it with `!wowmst link` yet?');
            }
            else if (typeof res.data === 'object') {
                // json returned but not an error code; success
                // initialize some empty strings, these will hold the tables
                console.log(res.data.metadata);
                const out = { 'dps': '', 'tank': '', 'heal': '' };
                const tables = ['dps', 'tank', 'heal'];
                const columns = ['rank', 'name', 'score'];
                const widths = {};
                tables.forEach(function(table) {
                    // start by initializing the table and settup up column headers
                    columns.forEach(function(column) {
                        out[table] += '|' + column;
                        const n = res.data.metadata[table + '_longest_' + column] - column.length;
                        if (n > 0) {
                            out[table] += ' '.repeat(n);
                            widths[table + column] = column.length + n;
                        }
                        else {
                            widths[table + column] = column.length;
                        }
                    });
                    out[table] += '|\n';
                    // add spacers
                    columns.forEach(function(column) {
                        out[table] += '|' + '-'.repeat(widths[table + column]);
                    });
                    out[table] += '|\n';
                    // set up each entry for each table
                    res.data[table].forEach(function(player) {
                        out[table] += '|';
                        columns.forEach(function(column) {
                            out[table] += player[column];
                            out[table] += ' '.repeat(widths[table + column] - player[column].toString().length);
                            out[table] += '|';
                        });
                        out[table] += '\n';
                    });
                    // talbe is constructed, put it in a multiline code block
                    out[table] = '```\n' + out[table];
                    out[table] += '```';
                });
                console.log(widths);
                console.log(out);
                return message.channel.send(
`DPS:
${out.dps}
Tank:
${out.tank}
Healer:
${out.heal}`,
                );
            }
            else {
                // catch for incase the bot's down (hope this works)
                    return message.channel.send('Something went horribly wrong. The bot is probably down.');
            }
        })
        .catch(err => {
            console.log(err);
        });
    }

    // -------------------------------
    // help command, list all commands
    // -------------------------------
    if (command === 'help' || command === '') {
        return message.channel.send(`General commands:
\`!wowmst\`
\`!wowmst help\`: list all bot commands (you are here)

Setup commands:
\`!wowmst new\`: instructions to set up your own spreadsheet to use with the bot.
\`!wowmst link\`: link a spreadsheet to be automatically updated and to use with the bot.

Spreadsheet commands:
\`!wowmst top10\`: get the top 10 players for each role from your linked spreadsheet.`);
    }
});

// log into Discord with the bot token
client.login(process.env.TOKEN);