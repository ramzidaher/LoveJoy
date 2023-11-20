document.getElementById('signInBtn').addEventListener('click', function() {
    // Implement sign-in logic
    // After successful sign-in, change the display
    document.querySelector('.user-auth').innerHTML = '<span>Welcome, User!</span>';
});

document.getElementById('signUpBtn').addEventListener('click', function() {
    // Implement sign-up logic
});


document.getElementById('userProfile').addEventListener('click', function() {
    document.querySelector('.dropdown-menu').classList.toggle('show');
});

document.addEventListener('DOMContentLoaded', function() {
    var userProfile = document.getElementById('userProfile');
    var dropdownMenu = document.querySelector('.dropdown-menu');

    userProfile.addEventListener('click', function(event) {
        dropdownMenu.style.display = 'block';
        dropdownMenu.style.opacity = '1';
        dropdownMenu.style.transform = 'translateY(0)';
        event.stopPropagation();
    });

    document.addEventListener('click', function() {
        dropdownMenu.style.opacity = '0';
        dropdownMenu.style.transform = 'translateY(-20px)';
        setTimeout(function() {
            dropdownMenu.style.display = 'none';
        }, 300); // Hide after transition
    });
});
