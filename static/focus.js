function addFocusEvents(highlighted, focused) {
    focused.addEventListener('focus', () => {
        highlighted.classList.add('focused');
    });
    focused.addEventListener('blur', () => {
        highlighted.classList.remove('focused');
    });
    for (const child of focused.children) {
        addFocusEvents(highlighted, child);
    }
}

document.addEventListener('DOMContentLoaded',() => {
    for (const item in document.getElementsByClassName('item')) {
        addFocusEvents(item, item);
    }
});
