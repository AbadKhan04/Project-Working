let speedChart; // Chart instance

// Function to fetch metrics and update DOM elements
async function fetchMetrics() {
    try {
        const response = await fetch('/metrics');
        const data = await response.json();

        // Update DOM elements
        document.getElementById('total-vehicles').textContent = data.total_vehicle_count || 0;
        document.getElementById('front-distance').textContent = data.front_distance || 0;
        document.getElementById('back-distance').textContent = data.back_distance || 0;
    } catch (error) {
        console.error('Error fetching metrics:', error);
    }
}

// Fetch logs and update table and chart
function fetchLogs() {
    fetch('/logs')
        .then((response) => response.json())
        .then((data) => {
            const logsTable = document.getElementById('logs-list');
            logsTable.innerHTML = ''; // Clear any existing logs

            const speeds = [];
            const labels = [];

            if (data.length > 0) {
                data.forEach((log) => {
                    // Add the log to the table
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${log.Timestamp}</td>
                        <td>${log.Vehicle_ID}</td>
                        <td>${log.Type}</td>
                        <td>${log.Speed}</td>
                        <td>${log.Overtaking_Event}</td>
                    `;
                    logsTable.appendChild(row);

                    // Add data to graph arrays
                    speeds.push(parseFloat(log.Speed));
                    labels.push(log.Vehicle_ID);
                });

                // Update the chart
                updateChart(labels, speeds);
            }
        })
        .catch((error) => {
            console.error('Error fetching logs:', error);
        });
}

// Initialize or update the speed chart
function updateChart(labels, data) {
    if (speedChart) {
        speedChart.data.labels = labels;
        speedChart.data.datasets[0].data = data;
        speedChart.update();
    } else {
        const ctx = document.getElementById('speedChart').getContext('2d');
        speedChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Vehicle Speed (km/h)',
                    data: data,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
            },
        });
    }
}

// Periodically fetch metrics and logs
setInterval(fetchMetrics, 1000);
setInterval(fetchLogs, 5000);
