// let speedChart; // Chart instance

// // Function to fetch metrics and update DOM elements
// async function fetchMetrics() {
//     try {
//         const response = await fetch('/metrics');
//         const data = await response.json();

//         // Update DOM elements
//         document.getElementById('total-vehicles').textContent = data.total_vehicle_count || 0;
//         document.getElementById('front-distance').textContent = data.front_distance || 0;
//         document.getElementById('back-distance').textContent = data.back_distance || 0;
//     } catch (error) {
//         console.error('Error fetching metrics:', error);
//     }
// }

// // Fetch logs and update table and chart
// function fetchLogs() {
//     fetch('/logs')
//         .then((response) => response.json())
//         .then((data) => {
//             const logsTable = document.getElementById('logs-list');
//             logsTable.innerHTML = ''; // Clear any existing logs

//             const speeds = [];
//             const labels = [];

//             if (data.length > 0) {
//                 data.forEach((log) => {
//                     // Add the log to the table
//                     const row = document.createElement('tr');
//                     row.innerHTML = `
//                         <td>${log.Timestamp}</td>
//                         <td>${log.Vehicle_ID}</td>
//                         <td>${log.Type}</td>
//                         <td>${log.Speed}</td>
//                         <td>${log.Overtaking_Event}</td>
//                     `;
//                     logsTable.appendChild(row);

//                     // Add data to graph arrays
//                     speeds.push(parseFloat(log.Speed));
//                     labels.push(log.Vehicle_ID);
//                 });

//                 // Update the chart
//                 updateChart(labels, speeds);
//             }
            
//         })
//         .catch((error) => {
//             console.error('Error fetching logs:', error);
//         });
// }

// // Initialize or update the speed chart
// function updateChart(labels, data) {
//     if (speedChart) {
//         speedChart.data.labels = labels;
//         speedChart.data.datasets[0].data = data;
//         speedChart.update();
//     } else {
//         const ctx = document.getElementById('speedChart').getContext('2d');
//         speedChart = new Chart(ctx, {
//             type: 'bar',
//             data: {
//                 labels: labels,
//                 datasets: [{
//                     label: 'Vehicle Speed (km/h)',
//                     data: data,
//                     backgroundColor: 'rgba(75, 192, 192, 0.6)',
//                     borderColor: 'rgba(75, 192, 192, 1)',
//                     borderWidth: 1,
//                 }],
//             },
//             options: {
//                 responsive: true,
//                 plugins: {
//                     legend: {
//                         display: true,
//                     },
//                 },
//                 scales: {
//                     y: {
//                         beginAtZero: true,
//                     },
//                 },
//             },
//         });
//     }
// }



// // Periodically fetch metrics and logs
// setInterval(fetchMetrics, 1000);
// setInterval(fetchLogs, 5000);

let speedChart; // Bar chart for speed
let pieChart;   // Pie chart for vehicle types

// Sample demo data
const demoLogs = [
    { Timestamp: '2025-05-05 14:12:30', Vehicle_ID: 'V001', Type: 'Car', Speed: '65', Overtaking_Event: 'Yes' },
    { Timestamp: '2025-05-05 14:15:12', Vehicle_ID: 'V002', Type: 'Truck', Speed: '50', Overtaking_Event: 'No' },
    { Timestamp: '2025-05-05 14:18:05', Vehicle_ID: 'V003', Type: 'Car', Speed: '72', Overtaking_Event: 'Yes' },
    { Timestamp: '2025-05-05 14:20:33', Vehicle_ID: 'V004', Type: 'Bus', Speed: '40', Overtaking_Event: 'No' },
    { Timestamp: '2025-05-05 14:22:50', Vehicle_ID: 'V005', Type: 'Truck', Speed: '55', Overtaking_Event: 'Yes' }
];

// Initialize everything on page load
document.addEventListener('DOMContentLoaded', () => {
    populateLogs(demoLogs);
    createSpeedChart(demoLogs);
    createPieChart(demoLogs);
});

// Populate the logs table
function populateLogs(logs) {
    const logsTable = document.getElementById('logs-list');
    logsTable.innerHTML = '';

    logs.forEach((log) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${log.Timestamp}</td>
            <td>${log.Vehicle_ID}</td>
            <td>${log.Type}</td>
            <td>${log.Speed}</td>
            <td>${log.Overtaking_Event}</td>
        `;
        logsTable.appendChild(row);
    });
}

// Create or update the speed bar chart
function createSpeedChart(logs) {
    const speeds = logs.map(log => parseFloat(log.Speed));
    const labels = logs.map(log => log.Vehicle_ID);

    const ctx = document.getElementById('speedChart').getContext('2d');
    speedChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Vehicle Speed (km/h)',
                data: speeds,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Create the pie chart showing vehicle type distribution
function createPieChart(logs) {
    const typeCounts = {};
    logs.forEach(log => {
        typeCounts[log.Type] = (typeCounts[log.Type] || 0) + 1;
    });

    const labels = Object.keys(typeCounts);
    const counts = Object.values(typeCounts);
    const colors = ['#8e2de2', '#ad99d7', '#b39ddb', '#ffcc80', '#a5d6a7']; // Add more if needed

    const ctx = document.getElementById('myPieChart').getContext('2d');
    pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'Vehicle Types',
                data: counts,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}


