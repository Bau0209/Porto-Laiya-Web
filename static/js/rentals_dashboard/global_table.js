// Function to load content into a popup frame
function loadPopup(url) {
    fetch(url)
        .then(response => response.text())
        .then(data => {
            document.getElementById('modalContent').innerHTML = `<div id="modalInnerContent">${data}</div>`;
        })
        .catch(error => console.error('Error loading popup:', error));
}


document.addEventListener("DOMContentLoaded", function () {
    fetchGuests();
});

async function fetchTransactions() {
    try {
        const response = await fetch('/get_transactions');  // Fetch transaction data from Flask
        if (!response.ok) throw new Error("HTTP error! Status: " + response.status);

        const transactions = await response.json();
        const tableBody = document.querySelector(".bookings-table tbody");
        tableBody.innerHTML = '';  // Clear existing rows

        let rowsHTML = '';  // Use a buffer string for better performance

        transactions.forEach((transaction, index) => {
            rowsHTML += `
            <tr class="table-row">
                <td class="table-cell">${index + 1}</td>
                <td class="table-cell">${transaction.transaction_id}</td>
                <td class="table-cell">${transaction.booker}</td>
                <td class="table-cell">${transaction.total_guests}</td>
                <td class="table-cell">${transaction.total_vehicles}</td>
                <td class="table-cell">${transaction.checkin_date}</td>
                <td class="table-cell">${transaction.checkout_date}</td>
                <td class="${transaction.status === 'COMMITTED' ? 'status-success' : transaction.status === 'CANCELLED' ? 'status-error' : 'status-pending'}">
                    ${transaction.status}
                </td>
                <td class="table-cell">₱${transaction.environmental_fee_total}</td>
                <td class="${transaction.environmental_fee_status === 'PAID' ? 'status-success' : 'status-error'}">
                    ${transaction.environmental_fee_status}
                </td>
                <td class="table-cell">
                    <button class="edit-button" data-bs-toggle="modal" data-bs-target="#modalContainer" 
                        onclick="loadPopup('/edit_transaction/${transaction.transaction_id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-button" data-bs-toggle="modal" data-bs-target="#deleteConfirmModal" 
                        onclick="setDeleteTransaction('${transaction.transaction_id}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                    <button class="view-more-button" data-bs-toggle="modal" data-bs-target="#modalContainer" 
                        onclick="loadPopup('/view_transaction/${transaction.transaction_id}')">
                        <i class="fas fa-ellipsis-h"></i>
                    </button>
                </td>
            </tr>`;
        });

        tableBody.innerHTML = rowsHTML;  // Update table once for better performance

    } catch (error) {
        console.error('Error fetching transactions:', error);
    }
}

async function fetchGuests() {
    try {
        const response = await fetch('/get_guests');  // Fetch guest data from Flask
        if (!response.ok) throw new Error("HTTP error! Status: " + response.status);

        const guests = await response.json();
        const tableBody = document.querySelector(".bookings-table tbody");
        tableBody.innerHTML = '';  // Clear existing rows

        let rowsHTML = '';  // Use a buffer string for better performance

        guests.forEach((guest, index) => {
            // Ensure all guest fields are safely inserted into the table
            const guestId = guest.guest_id || "N/A";
            const transactionId = guest.transaction_id || "N/A";
            const fullName = guest.full_name || "Unknown";
            const isBooker = guest.is_booker || "Unknown";
            const contactNumber = guest.contact_number || "N/A";
            const email = guest.email || "N/A";
            const checkinDate = guest.checkin_date || "N/A";
            const checkoutDate = guest.checkout_date || "N/A";

            rowsHTML += `
            <tr class="table-row">
                <td class="table-cell">${index + 1}</td>
                <td class="table-cell">${guestId}</td>
                <td class="table-cell">${transactionId}</td>
                <td class="table-cell">${fullName}</td>
                <td class="table-cell">${isBooker}</td>
                <td class="table-cell">${contactNumber}</td>
                <td class="table-cell">${email}</td>
                <td class="table-cell">${checkinDate}</td>
                <td class="table-cell">${checkoutDate}</td>
                <td class="table-cell">
                    <button class="edit-button" data-bs-toggle="modal" data-bs-target="#modalContainer" 
                        onclick="loadPopup('/edit_guest/${guestId}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-button" data-bs-toggle="modal" data-bs-target="#deleteConfirmModal" 
                        onclick="setDeleteGuest('${guestId}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                    <button class="view-more-button" data-bs-toggle="modal" data-bs-target="#modalContainer" 
                        onclick="loadPopup('/view_guest/${guestId}')">
                        <i class="fas fa-ellipsis-h"></i>
                    </button>
                </td>
            </tr>`;
        });

        tableBody.innerHTML = rowsHTML;  // Update table once for better performance

    } catch (error) {
        console.error('Error fetching guests:', error);
    }
}

function loadPopup(url) {
    document.getElementById("modalContent").innerHTML = `<iframe src="${url}" width="100%" height="400px" style="border:none;"></iframe>`;
}

function setDeleteGuest(guest_id) {
    if (confirm('Are you sure you want to delete this guest?')) {
        fetch(`/delete_guest/${guest_id}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Guest deleted successfully!');
                location.reload();  // Reload to update the table
            } else {
                alert('Failed to delete guest.');
            }
        })
        .catch(error => console.error('Error deleting guest:', error));
    }
}


function setDeleteTransaction(transaction_id) {
    if (confirm('Are you sure you want to delete this transaction?')) {
        fetch(`/delete_transaction/${transaction_id}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Transaction deleted successfully!');
                location.reload();  // Reload to update the table
            } else {
                alert('Failed to delete transaction.');
            }
        })
        .catch(error => console.error('Error deleting transaction:', error));
    }
}
