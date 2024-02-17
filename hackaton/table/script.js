const container = document.getElementById('table-container');
const fileInput = document.getElementById('file-input');

fileInput.addEventListener('change', function(event) {
  const file = event.target.files[0];

  if (!file) {
    return; // Handle no file selected case
  }

  const reader = new FileReader();

  reader.onload = function(e) {
    const data = e.target.result;
    const workbook = XLSX.read(data, { type: 'binary' });
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const jsonData = XLSX.utils.sheet_to_json(worksheet);

    const table = document.createElement('table');
    const headerRow = document.createElement('tr');
    for (const key in jsonData[0]) {
      const headerCell = document.createElement('th');
      headerCell.textContent = key;
      headerRow.appendChild(headerCell);
    }
    table.appendChild(headerRow);

    jsonData.forEach(row => {
      const tableRow = document.createElement('tr');
      Object.values(row).forEach(cellValue => {
        const tableCell = document.createElement('td');
        tableCell.textContent = cellValue;
        tableRow.appendChild(tableCell);
      });
      table.appendChild(tableRow);
    });

    container.innerHTML = ""; // Clear previous content
    container.appendChild(table);
  };

  reader.readAsBinaryString(file);
});
