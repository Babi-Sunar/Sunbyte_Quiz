// // menu toggle function of nav bar
// const menu = document.getElementById("nav");
// const menuBtn = document.getElementById("menuBtn");

// function toggleMenu(event) {
//     event.stopPropagation();   // Prevent the document click from firing
//     menu.classList.toggle("show");

//     // Close menu when clicking anywhere else
//     document.addEventListener("touchstart", function (event) {
//             menu.classList.remove("show");

//     });
// }
// ==========================
// Hamburger Menu
// ==========================

const menu = document.getElementById("nav");
const menuBtn = document.getElementById("menuBtn");

// Open / Close Menu
function toggleMenu(event) {
    event.stopPropagation();
    menu.classList.toggle("show");
}

// Prevent clicks/touches inside the menu from closing it
menu.addEventListener("click", function (event) {
    event.stopPropagation();
});

menu.addEventListener("touchstart", function (event) {
    event.stopPropagation();
});

// Close when clicking/touching anywhere outside
document.addEventListener("click", function () {
    menu.classList.remove("show");
});

document.addEventListener("touchstart", function () {
    menu.classList.remove("show");
});




// join-session
function joinSession() {
    let join_btn = document.getElementById("");
}

//connect form submit
function connect_form_submit() {
    let form = document.getElementById("connect-form");
    form.addEventListener('submit', function (event) {
        alert("🏆🎉Success! \n You've unlocked: 'Contact Form Completed' achievement. ");
    })
}

