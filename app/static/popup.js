function showPopup(id) {
    // Get DOM object
    let popup = document.getElementById(id);
    if (!popup || popup.style.getPropertyValue('display')==='block') return;

    // Hide others
    for (const other of document.getElementsByClassName('popup')) hidePopup(other.id);

    // Create background
    let bg = document.createElement('div');
    bg.onclick = () => hidePopup(id);
    bg.classList.add('popup_background');
    document.body.insertBefore(bg, popup);

    // Show popup
    popup.style.setProperty('display', 'block');
}

function hidePopup(popup) {
	// https://stackoverflow.com/questions/925734/whats-this-in-javascript-onclick

    // Get DOM object
    while (!popup.classList.contains('popup')) popup = popup.parentElement;
    if (popup.style.getPropertyValue('display')==='none') return;

    // Remove background
    for (const bg of document.getElementsByClassName('popup_background')) document.body.removeChild(bg);

    // Hide popup
    popup.style.setProperty('display', 'none');
}