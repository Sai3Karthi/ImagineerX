const dateTime = new Date('2024-02-20T10:00:00'); // Example date and time

checkAvailability(dateTime)
  .then((isAvailable) => {
    if (isAvailable) {
      console.log('User is available at that time');
    } else {
      console.log('User is busy at that time');
    }
  })
  .catch((error) => {
    console.error('Error checking availability:', error);
  });
