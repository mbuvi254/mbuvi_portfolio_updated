
  
    // Simulate page loading
    document.addEventListener("DOMContentLoaded", function () {
        setTimeout(function () {
            // Hide preloader
            document.getElementById('preloader').style.display = 'none';
            // Show content
            document.querySelector('.main').style.display = 'block';
        }, 2000); // Adjust the delay (in milliseconds) as needed
    });

    $(document).ready(function() {
        // Function to slide the box
        function slideBox() {
            $('.box').addClass('slide-in');
        }
    
        // Example usage
        setTimeout(slideBox, 1000); // Slide after 1 second
    });
