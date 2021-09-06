// Restricts input for the given textbox to 0-9; A-Z
function setInputFilter(textbox) {
    for (const event of ['input', 'keydown', 'keyup', 'mousedown', 'mouseup', 'select', 'contextmenu', 'drop']) {
        textbox.addEventListener(event, () => {
            let out = ''
            for (const char of textbox.value) {
                let upper = char.toUpperCase()
                if (('0' <= upper && '9' <= upper) || ('A' <= upper && 'Z' <= upper)) out += upper
            }
            textbox.value = out
        })
    }
}

document.addEventListener('DOMContentLoaded',() => {
    let keyBox = document.getElementById('new_user_key')
    if (keyBox) setInputFilter(keyBox)
})
