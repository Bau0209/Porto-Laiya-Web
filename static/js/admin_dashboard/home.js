// scripts.js

// Data for the Number of Transactions per Resort chart
window.onload = function() {
    // Array for month names
    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June', 
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    // Chart for Number of Transactions per Resort
    var ctx1 = document.getElementById('barChart1').getContext('2d');
    var barChart1 = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: transactionsPerResort.map(item => item.Business_Name), // Resort names from Flask data
            datasets: [{
                label: 'Number of Transactions', // Label for the bar graph
                data: transactionsPerResort.map(item => item.NumberOfTransactions), // Number of transactions
                backgroundColor: 'rgba(54, 162, 235, 0.6)', // Color of the bars
                borderColor: 'rgba(54, 162, 235, 1)', // Border color of bars
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true, // Ensure the y-axis starts at 0
                    ticks: {
                        font: {
                            size: 15 // Adjust this value for bigger/smaller numbers on the y-axis
                        }
                    }
                }
            }
        }
    });


    // Chart for Overall Number of Guests per Month
    var ctx2 = document.getElementById('barChart2').getContext('2d');
    var barChart2 = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: guestsPerMonth.map(item => monthNames[item.Month - 1]), // Convert month number to month name
            datasets: [{
                label: 'Number of Guests', // Label for the bar graph
                data: guestsPerMonth.map(item => item.NumberOfGuests), // Number of guests per month
                backgroundColor: 'rgba(255, 99, 132, 0.6)', // Color of the bars
                borderColor: 'rgba(255, 99, 132, 1)', // Border color of bars
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true // Ensure the y-axis starts at 0
                }
            }
        }
    });
};
