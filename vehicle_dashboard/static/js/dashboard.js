let speedChart = null;
let pieChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    setInterval(initDashboard, 5000); // auto refresh
});

async function initDashboard() {
    const logs = await fetchLogs();
    updateLogsTable(logs);
    // updateStats(logs);
    updateSpeedChart(logs);
    updatePieChart(logs);
    // await updateLiveStats();
}

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
setInterval(fetchMetrics, 500);


async function fetchLogs() {
    try {
        const response = await fetch('/get_logs');
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch logs:', error);
        return [];
    }
}

function updateLogsTable(logs) {
    const logsList = document.getElementById('logs-list');
    logsList.innerHTML = ''; // Clear old logs

    logs.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${log.timestamp}</td>
            <td>${log.vehicle_id}</td>
            <td>${log.vehicle_type}</td>
            <td>${log.speed} km/h</td>
            <td>${log.front}</td>
            <td>${log.back}</td>
            <td>${log.overtaking === 'True' ? 'Yes' : 'No'}</td>
        `;
        logsList.appendChild(row);
    });
}

// function updateStats(logs) {
//     const totalVehicles = logs.length;
//     document.getElementById('total-vehicles').textContent = totalVehicles;

//     if (totalVehicles > 0) {
//         const latest = logs[logs.length - 1];
//         document.getElementById('front-distance').textContent = latest.front;
//         document.getElementById('back-distance').textContent = latest.back;
//     } else {
//         document.getElementById('front-distance').textContent = '0';
//         document.getElementById('back-distance').textContent = '0';
//     }
// }

function createSpeedChart() {
    const ctx = document.getElementById('speedChart').getContext('2d');
    speedChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Speed (km/h)',
                data: [],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: { display: true, text: 'Time' },
                    ticks: { maxTicksLimit: 10 }
                },
                y: {
                    title: { display: true, text: 'Speed (km/h)' },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function updateSpeedChart(logs) {
    if (!speedChart) createSpeedChart();

    const timestamps = logs.map(log => log.timestamp);
    const speeds = logs.map(log => parseFloat(log.speed));

    speedChart.data.labels = timestamps;
    speedChart.data.datasets[0].data = speeds;
    speedChart.update();
}

function createPieChart() {
    const ctx = document.getElementById('myPieChart').getContext('2d');
    pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: ['#8e2de2', '#ad99d7', '#b39ddb', '#ffd54f', '#4db6ac']
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

function updatePieChart(logs) {
    if (!pieChart) createPieChart();

    const typeCounts = {};
    logs.forEach(log => {
        const type = log.vehicle_type;
        typeCounts[type] = (typeCounts[type] || 0) + 1;
    });

    const labels = Object.keys(typeCounts);
    const data = Object.values(typeCounts);

    pieChart.data.labels = labels;
    pieChart.data.datasets[0].data = data;
    pieChart.update();
}
