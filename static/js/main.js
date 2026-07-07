/* SunByte Quiz - small front-end helpers */

/**
 * Types the given text one character at a time into the element
 * with the given id, mimicking the "Join t|" effect seen on the
 * welcome screen.
 */
function typeWriter(text, elementId, speed = 60) {
    const el = document.getElementById(elementId);
    if (!el) return;

    let i = 0;
    el.textContent = '';

    function tick() {
        if (i < text.length) {
            el.textContent += text.charAt(i);
            i++;
            setTimeout(tick, speed);
        }
    }
    tick();
}

/**
 * Auto-uppercases session code inputs as the user types,
 * so codes are easy to read and always match how they were generated.
 */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[name="code"]').forEach((input) => {
        input.addEventListener('input', () => {
            input.value = input.value.toUpperCase();
        });
    });

    // Fade out flash messages after a few seconds.
    document.querySelectorAll('.message').forEach((msg) => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.6s ease';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 700);
        }, 4000);
    });
});
