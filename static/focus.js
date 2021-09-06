function addFocusEvents(highlighted, focused) {
    focused.addEventListener('focus', () => {
        highlighted.classList.add('focused');
    });
    focused.addEventListener('blur', () => {
        highlighted.classList.remove('focused');
    });
    for (const child in focused.childNodes) {
        addFocusEvents(highlighted, child);
    }
}

document.addEventListener('DOMContentLoaded',() => {
    for (const item in document.getElementsByClassName('item')) {
        addFocusEvents(item, item);
    }
})
