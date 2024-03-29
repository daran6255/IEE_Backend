document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("register-form");
    form.addEventListener("submit", function (event) {
        const name = document.getElementById("name").value.trim();
        const company = document.getElementById("company").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const password = document.getElementById("password").value;
        const confirm_password = document.getElementById("confirm_password").value;
        console.log(email);
        // Check if any field is empty
        if (name === "" || company === "" || email === "" || phone === "" || password === "" || confirm_password === "") {
            alert("All fields are required");
            event.preventDefault();
            return;
        }

        // Check if passwords match
        if (password !== confirm_password) {
            alert("Passwords do not match");
            event.preventDefault();
            return;
        }
    });
});
