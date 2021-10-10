function show_popup(id) {
    // Get DOM object
    let popup = document.getElementById(id);
    if (!popup || popup.style.getPropertyValue('display')==='block') return;

    // Hide others
    for (const other of document.getElementsByClassName('popup')) hide_popup(other.id);

    // Create background
    let bg = document.createElement('div');
    bg.onclick = () => hide_popup(id);
    bg.classList.add('popup_background');
    document.body.insertBefore(bg, popup);

    // Show popup
    popup.style.setProperty('display', 'block');
}

function hide_popup(id) {
    // Get DOM object
    let popup = id ? document.getElementById(id) : this;
    while (!popup.classList.contains('popup')) popup = popup.parentElement;
    if (popup.style.getPropertyValue('display')==='none') return;

    // Remove background
    for (const bg of document.getElementsByClassName('popup_background')) document.body.removeChild(bg);

    // Hide popup
    popup.style.setProperty('display', 'none');
}