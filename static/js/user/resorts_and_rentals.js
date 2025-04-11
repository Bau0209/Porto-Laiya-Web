const cardsPerPage = 4; // Number of cards to show per page 
const dataContainer = document.getElementById('data-container'); 
const pagination = document.getElementById('pagination'); 
const prevButton = document.getElementById('prev'); 
const nextButton = document.getElementById('next'); 
const pageNumbers = document.getElementById('page-numbers'); 
const pageLinks = document.querySelectorAll('.page-link'); 
const searchInput = document.getElementById('search-input');

const cards = Array.from(dataContainer.getElementsByClassName('card')); 
let filteredCards = [...cards]; // Start with all cards

// Calculate the total number of pages 
function calculateTotalPages() {
    return Math.ceil(filteredCards.length / cardsPerPage);
}
let totalPages = calculateTotalPages();
let currentPage = 1;

// Function to display cards for a specific page 
function displayPage(page) { 
    const startIndex = (page - 1) * cardsPerPage; 
    const endIndex = startIndex + cardsPerPage; 
    
    // Hide all cards initially
    cards.forEach(card => card.style.display = 'none');
    
    // Show only the cards for the current page
    filteredCards.slice(startIndex, endIndex).forEach((card, index) => { 
        if (index < cardsPerPage) {
            card.style.display = 'block'; 
        }
    }); 

    // Scroll to the top of the page
    window.scrollTo({ top: 0, behavior: 'smooth' });
} 


// Function to update pagination buttons and page numbers 
function updatePagination() { 
    pageNumbers.textContent = `Page ${currentPage} of ${totalPages}`; 
    prevButton.disabled = currentPage === 1; 
    nextButton.disabled = currentPage === totalPages; 
    pageLinks.forEach((link) => { 
        const page = parseInt(link.getAttribute('data-page')); 
        link.classList.toggle('active', page === currentPage); 
    }); 
} 

// Event listener for "Previous" button 
prevButton.addEventListener('click', () => { 
    if (currentPage > 1) { 
        currentPage--; 
        displayPage(currentPage); 
        updatePagination(); 
    } 
}); 

// Event listener for "Next" button 
nextButton.addEventListener('click', () => { 
    if (currentPage < totalPages) { 
        currentPage++; 
        displayPage(currentPage); 
        updatePagination(); 
    } 
}); 

// Event listener for page number buttons 
pageLinks.forEach((link) => { 
    link.addEventListener('click', (e) => { 
        e.preventDefault(); 
        const page = parseInt(link.getAttribute('data-page')); 
        if (page !== currentPage) { 
            currentPage = page; 
            displayPage(currentPage); 
            updatePagination(); 
        } 
    }); 
}); 

// Search and Filter Functionality
searchInput.addEventListener('input', () => {
    const query = searchInput.value.toLowerCase();
    filteredCards = cards.filter(card => {
        const cardText = card.textContent.toLowerCase();
        return cardText.includes(query);
    });
    totalPages = calculateTotalPages();
    currentPage = 1;
    displayPage(currentPage);
    updatePagination();
});


function viewMore(resortName) {
    window.location.href = `/user_resorts_and_rentals_info?resort_name=${encodeURIComponent(resortName)}`;
}

// Initial page load 
displayPage(currentPage); 
updatePagination();
