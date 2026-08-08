// No JavaScript is required for the signup form yet.
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("signupForm");

    form.addEventListener("submit", function (event) {
        const password1 = document.getElementById("password1").value;
        const password2 = document.getElementById("password2").value;

        if (password1 !== password2) {
            event.preventDefault();
            alert("Passwords do not match.");
        }
    });
});