console.log("Hybrid ML Project Loaded");

document.addEventListener("DOMContentLoaded", () => {

    let cards = document.querySelectorAll(".card");

    cards.forEach((card) => {

        card.addEventListener("mouseenter", () => {

            card.style.transform = "scale(1.05)";

        });

        card.addEventListener("mouseleave", () => {

            card.style.transform = "scale(1)";

        });

    });

});

/* SIDEBAR ACTIVE EFFECT */

let links = document.querySelectorAll(".sidebar ul li a");

links.forEach((link) => {

    link.addEventListener("click", () => {

        links.forEach((l) => {

            l.classList.remove("active-link");

        });

        link.classList.add("active-link");

    });

});