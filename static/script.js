// This script will add a bungee effect to the form and track mouse movements for interactive background effects

// Ripple Effect on Form Hover
document.addEventListener('mousemove', function (e) {
    const form = document.querySelector('main form');
    const { left, top, width, height } = form.getBoundingClientRect();
    const x = (e.clientX - left) / width * 100;
    const y = (e.clientY - top) / height * 100;

    // Applying water-like ripple effect based on mouse movement
    form.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(255, 255, 255, 0.1), transparent 70%)`;
});

document.addEventListener('mouseleave', function () {
    const form = document.querySelector('main form');
    // Reset the background when the mouse leaves the form
    form.style.background = 'rgba(255, 255, 255, 0.1)';
});

// Bungee effect when hovering over the form
const form = document.querySelector('main form');
form.addEventListener('mouseover', function () {
    form.style.transform = 'scale(1.05)';
    form.style.boxShadow = '0 20px 35px rgba(0, 0, 0, 0.3)';
});

form.addEventListener('mouseleave', function () {
    form.style.transform = 'scale(1)';
    form.style.boxShadow = '0 15px 25px rgba(0, 0, 0, 0.2)';
});

// Add animation effect for buttons
const buttons = document.querySelectorAll('button');
buttons.forEach(button => {
    button.addEventListener('mouseover', function () {
        button.style.backgroundColor = '#4e73df'; // Change color on hover
        button.style.transform = 'translateY(-3px)'; // Slight lift
    });

    button.addEventListener('mouseleave', function () {
        button.style.backgroundColor = '#36b9cc'; // Reset background color
        button.style.transform = 'translateY(0)'; // Reset the position
    });
});

// Ensure form inputs and buttons remain interactive
const inputs = document.querySelectorAll('input, select');
inputs.forEach(input => {
    input.addEventListener('focus', function () {
        input.style.boxShadow = '0 0 10px 2px rgba(255, 255, 255, 0.5)'; // Add glow on focus
    });

    input.addEventListener('blur', function () {
        input.style.boxShadow = 'none'; // Remove glow after input focus is lost
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const flashMessages = document.querySelectorAll(".flash-message");

    // Fade out messages after 5 seconds if they haven’t faded already
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = "0";
            message.style.transform = "translateY(-20px)";
        }, 5000); // Message disappears after 5 seconds
    });
});
