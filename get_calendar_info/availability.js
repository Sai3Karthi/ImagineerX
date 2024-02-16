// Function to read data from Excel file (using a library like SheetJS)
async function readExcelData() {
  const filePath = document.getElementById('excelFile').value;

  if (!filePath) {
    alert('Please specify the path to the Excel file.');
    return;
  }

  const data = await readFileAsync(filePath);
  // Extract user names and schedules from the parsed data
  return processExcelData(data);
}

// Function to read file asynchronously
function readFileAsync(filePath) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', filePath, true);
    xhr.responseType = 'arraybuffer';

    xhr.onload = function () {
      if (xhr.status === 200) {
        const data = new Uint8Array(xhr.response);
        const workbook = XLSX.read(data, { type: 'array' });
        resolve(workbook);
      } else {
        reject(new Error(`Failed to fetch file. Status: ${xhr.status}`));
      }
    };

    xhr.onerror = function () {
      reject(new Error('Failed to fetch file.'));
    };

    xhr.send();
  });
}

// Helper function to parse time in HH:mm format
function parseTime(timeString) {
  const [hours, minutes] = timeString.split(':').map(Number);
  const date = new Date();
  date.setHours(hours);
  date.setMinutes(minutes);
  date.setSeconds(0); // Assuming seconds are not provided in the Excel file
  return date;
}

// Function to convert decimal time to HH:mm format
function convertDecimalToTime(decimalTime) {
  if (typeof decimalTime === 'undefined' || isNaN(decimalTime)) {
    return 'N/A';
  }

  const totalMinutes = decimalTime * 24 * 60;
  const hours = Math.floor(totalMinutes / 60);
  const minutes = Math.round(totalMinutes % 60);
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

// Function to process data and return an object with user names and schedules
function processExcelData(workbook) {
  const userData = {};
  const sheetName = workbook.SheetNames[0];
  const sheetData = workbook.Sheets[sheetName];

  if (!sheetData) {
    console.error('Sheet data is undefined. Check if the sheet name is correct in your Excel file.');
    return { userData };
  }

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  // Iterate through rows starting from the second row (index 2)
  for (let row = 2; ; row++) {
    const nameCell = sheetData[`A${row}`];

    // Check if the cell in the first column is present
    if (!nameCell || typeof nameCell.v === 'undefined') {
      console.warn(`Missing name for cell A${row}. Skipping.`);
      break;
    }

    const name = nameCell.v;

    // Initialize user data for the current name
    if (!userData[name]) {
      userData[name] = {};
    }

    console.log(`Processing row ${row} for ${name}`);

    for (let dayIndex = 0; dayIndex < daysOfWeek.length; dayIndex++) {
      const startColIndex = 2 + dayIndex * 2;
      const startTimeCell = sheetData[`${XLSX.utils.encode_col(startColIndex - 1)}${row}`];
      const endTimeCell = sheetData[`${XLSX.utils.encode_col(startColIndex)}${row}`];

      // Log the cell values for debugging
      console.log(`  ${daysOfWeek[dayIndex]}: ${XLSX.utils.encode_col(startColIndex)}${row} - Start: ${startTimeCell ? startTimeCell.v : 'N/A'}, End: ${endTimeCell ? endTimeCell.v : 'N/A'}`);

      // Check if the cells for start time and end time exist
      if (!startTimeCell && !endTimeCell) {
        console.warn(`Missing start and end time for row ${row}. Skipping.`);
        continue;
      }

      const startTime = startTimeCell ? convertDecimalToTime(parseFloat(startTimeCell.v)) : 'N/A';
      const endTime = endTimeCell ? convertDecimalToTime(parseFloat(endTimeCell.v)) : 'N/A';

      userData[name][daysOfWeek[dayIndex]] = { startTime, endTime };
    }
  }

  return { userData };
}

// Function to check if a user is busy at a specific time
function isUserBusy(userName, dateTime, userSchedules) {
  const dayOfWeek = dateTime.toLocaleString('en-US', { weekday: 'long' });
  const userSchedule = userSchedules[userName];

  if (userSchedule && userSchedule[dayOfWeek]) {
    const startTime = userSchedule[dayOfWeek].startTime;
    const endTime = userSchedule[dayOfWeek].endTime;

    // Check for 'N/A' values
    if (startTime === 'N/A' || endTime === 'N/A') {
      console.log(`User ${userName} is available at that time`);
      return false;
    }

    const parsedStartTime = parseTime(startTime);
    const parsedEndTime = parseTime(endTime);

    console.log(`dateTime: ${dateTime}`);
    console.log(`parsedStartTime: ${parsedStartTime}`);
    console.log(`parsedEndTime: ${parsedEndTime}`);

    // Extract hours and minutes from the date objects
    const dateTimeHours = dateTime.getHours();
    const dateTimeMinutes = dateTime.getMinutes();
    const parsedStartTimeHours = parsedStartTime.getHours();
    const parsedStartTimeMinutes = parsedStartTime.getMinutes();
    const parsedEndTimeHours = parsedEndTime.getHours();
    const parsedEndTimeMinutes = parsedEndTime.getMinutes();

    // Check if the current time is within the availability range
    const isBusy =
      (dateTimeHours > parsedStartTimeHours ||
        (dateTimeHours === parsedStartTimeHours && dateTimeMinutes >= parsedStartTimeMinutes)) &&
      (dateTimeHours < parsedEndTimeHours ||
        (dateTimeHours === parsedEndTimeHours && dateTimeMinutes <= parsedEndTimeMinutes));

    console.log(`isBusy: ${isBusy}`);

    return isBusy;
  }

  return false;
}

document.addEventListener('DOMContentLoaded', async () => {
  const userSchedules = await readExcelData();
  const userDropdown = document.getElementById('userList');
  const checkAvailabilityButton = document.getElementById('checkAvailabilityButton');
  const availableUsersList = document.getElementById('availableUsersList');
  const availabilityResult = document.getElementById('availabilityResult'); // Added this line

  for (const userName in userSchedules.userData) {
    const option = document.createElement('option');
    option.value = userName;
    option.text = userName;
    userDropdown.add(option);
  }

  // Inside the checkAvailabilityButton click event handler
  checkAvailabilityButton.addEventListener('click', async () => {
    const userName = userDropdown.value; // Added this line
    const dateTime = new Date(document.getElementById('dateTimeInput').value);

    // Wait for readExcelData to complete before checking availability
    const userSchedules = await readExcelData();
    const isBusy = isUserBusy(userName, dateTime, userSchedules.userData); // Updated this line

    const resultText = isBusy
      ? `${userName} is busy at that time`
      : `${userName} is available at that time`;

    console.log('Result Text:', resultText);

    availabilityResult.textContent = resultText; // Updated this line

    // Update available users list
    availableUsersList.innerHTML = '';

    for (const user in userSchedules.userData) {
      if (!isUserBusy(user, dateTime, userSchedules.userData)) {
        const listItem = document.createElement('li');
        listItem.textContent = user;
        availableUsersList.appendChild(listItem);
      }
    }

    // Show/hide the user list section
    availableUsersList.style.display = availableUsersList.children.length > 0 ? 'block' : 'none';
  });
});

