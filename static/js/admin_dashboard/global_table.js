// Function to load content into a popup frame
function loadPopup(url) {
    fetch(url)
        .then(response => response.text())
        .then(data => {
            document.getElementById('modalContent').innerHTML = `<div id="modalInnerContent">${data}</div>`;
        })
        .catch(error => console.error('Error loading popup:', error));
}


function searchBookings() {
    const query = document.getElementById("searchInput").value.toLowerCase();
    const rows = document.querySelectorAll('.bookings-table tbody tr');

    rows.forEach(row => {
        let matchFound = false;

        row.querySelectorAll("td").forEach(cell => {
            if (cell.textContent.toLowerCase().includes(query)) {
                matchFound = true; // If any cell contains the query, keep the row visible
            }
        });

        row.style.display = matchFound ? "" : "none"; // Show row if a match is found, else hide
    });
}


let guestIdToDelete = null;

// Set the guest_id in the modal
function setGuestId(guestId) {
    guestIdToDelete = guestId;
}

// Handle the deletion
function deleteGuest() {
    if (guestIdToDelete) {
        fetch(`/delete_guest/${guestIdToDelete}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                // Show success message
                alert('Guest deleted successfully!');

                // Remove the guest row from the table dynamically
                const guestRow = document.getElementById(`guest-row-${guestIdToDelete}`);
                if (guestRow) {
                    guestRow.remove();  // Remove row from the table
                }

                // Close the modal properly
                let modal = document.getElementById("deleteConfirmModal");
                let modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();  // Hide modal
                }

            } else {
                alert('Error deleting guest: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error deleting the guest.');
        });
    }
}

function setPropertyId(propertyCode) {
    // Set the property ID in the hidden input field to be used for deletion
    var deletePropertyId = document.getElementById("deletePropertyId");
    if (deletePropertyId) {
        deletePropertyId.value = propertyCode;
    } else {
        console.error('Hidden input for property ID not found');
    }
}


function confirmDelete() {
    // Get the property ID from the hidden input field
    var propertyId = document.getElementById("deletePropertyId");

    // Check if the hidden input exists
    if (propertyId) {
        propertyId = propertyId.value;

        // Make an AJAX request to the server to delete the property
        fetch('/delete_property/' + propertyId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // If delete is successful, show success message
                showSuccessMessage('Property deleted successfully!');
                
                // Optionally, remove the property row from the table
                var row = document.getElementById("property-row-" + propertyId);
                if (row) {
                    row.remove();  // Remove the row from the table
                }
                location.reload();
            } else {
                alert('Failed to delete property');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to delete property');
        });
    } else {
        console.error('Property ID not found!');
    }
}

function showSuccessMessage(message) {
    // Create the success message div
    var successMessageDiv = document.createElement('div');
    successMessageDiv.classList.add('alert', 'alert-success');
    successMessageDiv.setAttribute('role', 'alert');
    successMessageDiv.textContent = message;

    // Append the message to the body or a specific container
    document.body.appendChild(successMessageDiv);

    // Optionally, remove the message after 5 seconds
    setTimeout(function() {
        successMessageDiv.remove();
    }, 5000);
}
