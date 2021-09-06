// Restricts input for the given textbox to 0-9; A-Z
function setInputFilter(textbox) {
    for (const event of ['input', 'keydown', 'keyup', 'mousedown', 'mouseup', 'select', 'contextmenu', 'drop']) {
        textbox.addEventListener(event, () => {
            let out = '';
            for (const char of textbox.value) {
                let isNumber = '0' <= char && char <= '9';
                let isUpper = 'A' <= char && char <= 'Z';
                let isLower = 'a' <= char && char <= 'z';
                if (isNumber || isUpper || isLower) out += char.toUpperCase();
            }
            textbox.value = out.substr(0, 8);
        });
    }
}

document.addEventListener('DOMContentLoaded',() => {
    let keyBox = document.getElementById('new_user_key');
    if (keyBox) setInputFilter(keyBox);
});
