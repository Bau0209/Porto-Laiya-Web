document.addEventListener("DOMContentLoaded", function() {
    const pricePerDay = parseFloat(document.getElementById('price').getAttribute('data-price')); // Price per day
    const environmentalFeePerGuest = 20; // Fee per guest

    function calculateNights(checkInDate, checkOutDate) {
        const checkIn = new Date(checkInDate);
        const checkOut = new Date(checkOutDate);
        const timeDifference = checkOut - checkIn;
        const daysDifference = timeDifference / (1000 * 3600 * 24);
        return daysDifference > 0 ? daysDifference : 0;
    }

    function countCompletedGuests() {
        const guestForms = document.querySelectorAll(".form-content.plus-guest");
        let filledGuestCount = 1; // Start at 1 for the booker

        guestForms.forEach(guestForm => {
            const inputs = guestForm.querySelectorAll("input[type='text'], input[type='number'], input[type='tel'], input[type='email']");
            const isFilled = Array.from(inputs).every(input => input.value.trim() !== ""); // Check if all fields are filled

            if (isFilled) {
                filledGuestCount++; // Increase count only for completely filled guest forms
            }
        });

        return filledGuestCount;
    }

    function updateTotal() {
        const checkIn = document.getElementById('checkIn').value;
        const checkOut = document.getElementById('checkOut').value;
        const numGuests = countCompletedGuests(); // Get the actual guest count
    
        console.log('Check-in:', checkIn);
        console.log('Check-out:', checkOut);
        console.log('Number of guests:', numGuests);
    
        if (checkIn && checkOut && numGuests > 0) {
            const nights = calculateNights(checkIn, checkOut);
            const dayRate = nights * pricePerDay;
            const environmentalFee = numGuests * environmentalFeePerGuest;
            const total = dayRate + environmentalFee;

            console.log("Updating totals...");
            console.log("Nights:", nights, "Guests:", numGuests, "Day Rate:", dayRate, "Env Fee:", environmentalFee, "Total:", total);

            // Update the inputs properly
            document.getElementById('day').value = `Php ${dayRate.toLocaleString()}`;
            document.getElementById('environmentalFee').value = `Php ${environmentalFee.toLocaleString()}`;
            document.getElementById('totalAmount').value = `Php ${total.toLocaleString()}`;
        }
    }    

    // Event listeners for check-in, check-out, and guest input fields
    document.getElementById('checkIn').addEventListener('change', updateTotal);
    document.getElementById('checkOut').addEventListener('change', updateTotal);

    document.querySelectorAll(".form-content.plus-guest input").forEach(input => {
        input.addEventListener("input", updateTotal);
    });

    document.getElementById('add-guest').addEventListener("click", function() {
        setTimeout(() => {
            // Attach event listeners to new guest inputs
            document.querySelectorAll(".form-content.plus-guest input").forEach(input => {
                input.addEventListener("input", updateTotal);
            });

            updateTotal();
        }, 100);
    });

    // Initialize the calculations on page load
    updateTotal();
});


