document.addEventListener("DOMContentLoaded", () => {
    const thumbnails = document.querySelectorAll(".carousel-thumbnails img");
    const mainImage = document.querySelector("#main-image");

    // Change main image on thumbnail click
    thumbnails.forEach((thumbnail, index) => {
        thumbnail.addEventListener("click", () => {
            const fullImageUrl = thumbnail.getAttribute("data-full");
            mainImage.setAttribute("src", fullImageUrl);

            // Highlight the selected thumbnail
            thumbnails.forEach(t => t.classList.remove("thumbnail-highlight"));
            thumbnail.classList.add("thumbnail-highlight");
        });
    });
});

// Save description
document.getElementById('save-description').addEventListener('click', function() {
    const description = document.getElementById('description-textbox').value;
    fetch('/update_description', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            description: description,
        }),
    })
    .then(response => response.json())
    .then(data => alert('Description updated successfully'))
    .catch(error => console.error('Error:', error));
});

// Save price
document.getElementById('save-price').addEventListener('click', function() {
    const price = document.getElementById('night-price').value;
    fetch('/update_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            price: price,
        }),
    })
    .then(response => response.json())
    .then(data => alert('Price updated successfully'))
    .catch(error => console.error('Error:', error));
});
