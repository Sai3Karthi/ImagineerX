const { google } = require('@googleapis/calendar'); // Assuming you installed the library

// Replace with your actual API key and user's calendar ID
const apiKey = 'AIzaSyDT50I_94RRLL4ePk2gHjyMpGjIEKHXftE';
const calendarId = 'user@example.com'; // Replace with actual calendar ID

const client = new google.auth.OAuth2(apiKey);
