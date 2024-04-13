document.addEventListener("DOMContentLoaded", function () {
    let currentImageIndex = 0;
    let isManualClick = false;
    const images = document.querySelectorAll('.carousel-image');
    const totalImages = images.length;
    let timer;

    function showImage(index) {
        images.forEach(image => image.classList.remove('active'));
        images[index].classList.add('active');
    }

    function nextImage() {
        currentImageIndex = (currentImageIndex + 1) % totalImages;
        showImage(currentImageIndex);
        resetTimer();
    }

    function prevImage() {
        currentImageIndex = (currentImageIndex - 1 + totalImages) % totalImages;
        showImage(currentImageIndex);
        resetTimer();
    }

    function resumeAutomaticSlide() {
        timer = setInterval(nextImage, 1000);
    }

    function resetTimer() {
        clearInterval(timer);
        timer = setTimeout(resumeAutomaticSlide, 2000); // Resume automatic slide after 5 seconds
    }

    resumeAutomaticSlide(); // Start automatic slide

    document.getElementById('prev').addEventListener('click', function () {
        isManualClick = true;
        prevImage();
    });

    document.getElementById('next').addEventListener('click', function () {
        isManualClick = true;
        nextImage();
    });

    document.getElementById('image-carousel').addEventListener('click', function () {
        resetTimer();
    });
});

var swiper = new Swiper(".course-slider", {
    spaceBetween:20,
    grabCursor:true,
    loop:true,
    pagination: {
        el: ".swiper-pagination",  
    clickable:true,
    },
    breakpoints: {
        540:{
            slidesPerView:1,
        },
        768:{
            slidesPerView:2,
        },
        1024:{
            slidesPerView:3,
        },                
    }
});

