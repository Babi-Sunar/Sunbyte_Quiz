const form = document.getElementById("loginForm");


// form submit
form.addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent page reload

    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let rememberMe = document.getElementById("remember").checked;

    // if no users
    if (!localStorage.getItem("users")) {
        alert("Sorry, no user found \nSign up first.");
        return;
    }
    // fetch all users
    let users = JSON.parse(localStorage.getItem("users"));
    const existingUser = users.find(
        user => user.email === email
    );

    if (existingUser) {
        const matchPassword = users.find(
            user => user.email === email && user.password === password
        );
        if (matchPassword) {
            alert("login successful !");
            name = users.find(user => user.email === email).name;
            sessionStorage.setItem("username", name);
            window.location.href = "user_dashboard.html";
        }
        else {
            alert("Incorrect username or password !");
        }
    } else {
        alert("Sorry, no user found \nSign up first.");
        return;
    }
});

