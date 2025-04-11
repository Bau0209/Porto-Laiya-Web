document.addEventListener("DOMContentLoaded", () => {
  const thumbnails = document.querySelectorAll(".carousel-thumbnails img");
  const mainImage = document.querySelector("#main-image");

  // Change the main image when a thumbnail is clicked
  thumbnails.forEach(thumbnail => {
    thumbnail.addEventListener("click", function () {
      mainImage.src = this.dataset.full;

      // Remove highlight from all thumbnails
      thumbnails.forEach(img => img.classList.remove("thumbnail-highlight"));

      // Add highlight to the clicked thumbnail
      this.classList.add("thumbnail-highlight");
    });
  });

  // Enable full-screen viewing when clicking the main image
  mainImage.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      mainImage.requestFullscreen().catch(err => console.error("Fullscreen failed:", err));
    } else {
      document.exitFullscreen();
    }
  });
});
