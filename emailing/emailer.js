const fs = require('fs');
const readline = require('readline');
const {google} = require('googleapis');
const MailComposer = require('nodemailer/lib/mail-composer');
var ArgumentParser = require('argparse').ArgumentParser;


// If modifying these scopes, delete token.json.
const SCOPES = [
	'https://mail.google.com',
	'https://www.googleapis.com/auth/gmail.readonly'
];
// The file token.json stores the user's access and refresh tokens, and is
// created automatically when the authorization flow completes for the first
// time.
const TOKEN_PATH = 'token.json';

// Load client secrets from a local file.
fs.readFile('/Users/thechetan/Documents/blog-book/emailing/credentials.json', (err, content) => {
	if (err) return console.log('Error loading client secret file:', err);
	// Authorize a client with credentials, then call the Gmail API.
	authorize(JSON.parse(content), sendAttachmentEmail);
});

/**
 * Create an OAuth2 client with the given credentials, and then execute the
 * given callback function.
 * @param {Object} credentials The authorization client credentials.
 * @param {function} callback The callback to call with the authorized client.
 */
function authorize(credentials, callback) {
	const {client_secret, client_id, redirect_uris} = credentials.installed;
	const oAuth2Client = new google.auth.OAuth2(
		client_id, client_secret, redirect_uris[0]);

	// Check if we have previously stored a token.
	fs.readFile(TOKEN_PATH, (err, token) => {
		if (err) return getNewToken(oAuth2Client, callback);
		oAuth2Client.setCredentials(JSON.parse(token));
		callback(oAuth2Client);
	});
}

/**
 * Get and store new token after prompting for user authorization, and then
 * execute the given callback with the authorized OAuth2 client.
 * @param {google.auth.OAuth2} oAuth2Client The OAuth2 client to get token for.
 * @param {getEventsCallback} callback The callback for the authorized client.
 */
function getNewToken(oAuth2Client, callback) {
	const authUrl = oAuth2Client.generateAuthUrl({
		access_type: 'offline',
		scope: SCOPES,
	});
	console.log('Authorize this app by visiting this url:', authUrl);
	const rl = readline.createInterface({
		input: process.stdin,
		output: process.stdout,
	});
	rl.question('Enter the code from that page here: ', (code) => {
		rl.close();
		oAuth2Client.getToken(code, (err, token) => {
			if (err) return console.error('Error retrieving access token', err);
			oAuth2Client.setCredentials(token);
			// Store the token to disk for later program executions
			fs.writeFile(TOKEN_PATH, JSON.stringify(token), (err) => {
				if (err) return console.error(err);
				console.log('Token stored to', TOKEN_PATH);
			});
			callback(oAuth2Client);
		});
	});
}

function build_input_params() {
	var parser = new ArgumentParser({
		version: '0.0.1',
		addHelp:true,
		description: 'Argparse example'
	});
	parser.addArgument(
		[ '-t', '--to' ],{help: 'Email to who', required:false}
	);
	parser.addArgument(
		[ '-s', '--subject' ],{help: 'Email Subject', required:false}
	);
	parser.addArgument(
		[ '-a', '--attachment' ],{help: 'File path for the attachment', required:false}
	);
	parser.addArgument(
		[ '--html' ],{help: 'Html body of the email', required:false}
	);
	parser.addArgument(
		[ '--body' ],{help: 'Text body for non html clents or normal text body', required:false}
	);
	var args = parser.parseArgs();
	console.dir(args);
	return args

}

function sendAttachmentEmail(auth) {

	input_params = build_input_params()
	debugger;
	

	let mail = new MailComposer(
		{
			to: input_params.to,
			text: input_params.body,
			html: input_params.html,
			subject: input_params.subject,
			attachments: [
				{
					path: input_params.attachment
				}
			]
		});

	mail.compile().build( (error, msg) => {
		if (error) return console.log('Error compiling email ' + error);

		const encodedMessage = Buffer.from(msg)
			.toString('base64')
			.replace(/\+/g, '-')
			.replace(/\//g, '_')
				.replace(/=+$/, '');

				const gmail = google.gmail({version: 'v1', auth});
				gmail.users.messages.send({
					userId: 'me',
					resource: {
						raw: encodedMessage,
					}
				}, (err, result) => {
					if (err) return console.log('NODEMAILER - The API returned an error: ' + err);

					console.log("NODEMAILER - Sending email reply from server:", result.data);
				});

	})



}
