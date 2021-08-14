for (const item in document.getElementsByClassName('item')) {
    addFocusEvents(item, item);
}

function addFocusEvents(focusItem, element) {
    element.addEventListener('focus', () => {
        focusItem.classList.add('focused');
    });
    element.addEventListener('blur', () => {
        focusItem.classList.remove('focused');
    });
    for (const child in element.childNodes) {
        addFocusEvents(focusItem, child);
    }
}
